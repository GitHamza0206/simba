import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys

logger = logging.getLogger(__name__)

# Always use the current working directory as the base directory
BASE_DIR = Path.cwd()
logger.info(f"Using current working directory as base: {BASE_DIR}")

# Load .env from the base directory
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"✅ Successfully loaded environment variables from: {env_path}")
else:
    logger.warning(f"⚠️ No .env file found at: {env_path}")
    logger.info("Using default environment variables or system environment variables")

# Validate critical environment variables
critical_env_vars = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'REDIS_HOST': os.getenv('REDIS_HOST'),
    'CELERY_BROKER_URL': os.getenv('CELERY_BROKER_URL'),
    'CELERY_RESULT_BACKEND': os.getenv('CELERY_RESULT_BACKEND')
}

for var_name, var_value in critical_env_vars.items():
    if var_value:
        logger.info(f"✅ Environment variable loaded: {var_name}")
    else:
        logger.warning(f"⚠️ Missing environment variable: {var_name}")



class ProjectConfig(BaseModel):
    name: str = "Simba"
    version: str = "1.0.0"
    api_version: str = "/api/v1"

class PathConfig(BaseModel):
    base_dir: Path = Field(default_factory=lambda: BASE_DIR)
    faiss_index_dir: Path = Field(default="vector_stores/faiss_index")
    vector_store_dir: Path = Field(default="vector_stores")
    upload_dir: Path = Field(default="uploads")

    def __init__(self, **data):
        super().__init__(**data)
        # Resolve all paths relative to base directory
        self.faiss_index_dir = self.base_dir / self.faiss_index_dir
        self.vector_store_dir = self.base_dir / self.vector_store_dir
        self.upload_dir = self.base_dir / self.upload_dir
        
        # Create directories if they don't exist
        for path in [self.faiss_index_dir, self.vector_store_dir, self.upload_dir]:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {path}")

class LLMConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  

    provider: str = Field(default="openai")
    model_name: str = Field(default="gpt-4")
    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key from environment variables"
    )
    base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for LLM service (e.g., Ollama server)"
    )
    temperature: float = Field(default=0.0)
    streaming: bool = Field(default=True)
    max_tokens: Optional[int] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  

    provider: str = "openai"
    model_name: str = "text-embedding-3-small"
    device: str = "cpu"
    
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class VectorStoreConfig(BaseModel):
    provider: str = "faiss"
    collection_name: str = "migi_collection"
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class ChunkingConfig(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 50

class RetrievalConfig(BaseModel):
    k: int = 5


class DatabaseConfig(BaseModel):
    provider: str = "litedb"  # or "sqlite"
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class CelerySettings(BaseModel):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"

class Settings(BaseSettings):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    celery: CelerySettings = Field(default_factory=CelerySettings)

    @field_validator('celery')
    @classmethod
    def validate_celery(cls, v, values):
        if not v.broker_url:
            raise ValueError("Celery broker URL is required")
        return v

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> 'Settings':
        """Load settings from config.yaml in the base directory."""
        config_file = BASE_DIR / "config.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found at {config_file}. "
                "Please ensure config.yaml exists in the project root directory."
            )
        
        logger.info(f"Loading configuration from {config_file}")
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}
        
        # Ensure base_dir is set to BASE_DIR
        if "paths" not in config_data:
            config_data["paths"] = {}
        config_data["paths"]["base_dir"] = str(BASE_DIR)
        
        return cls(**config_data)

# Create global settings instance
try:
    settings = Settings.load_from_yaml()
except FileNotFoundError as e:
    logger.error(str(e))
    raise
except Exception as e:
    logger.error(f"Failed to load configuration file: {e}")
    raise

# # Ensure directories exist
# def ensure_directories():
#     """Create necessary directories if they don't exist."""
#     directories = [
#         settings.paths.faiss_index_dir,
#         settings.paths.vector_store_dir
#     ]
    
#     for directory in directories:
#         directory.mkdir(parents=True, exist_ok=True)
#         logger.info(f"Ensured directory exists: {directory}")

# # Create directories on import
# ensure_directories()

if __name__ == "__main__":
    print("\nCurrent Settings:")
    print(f"Base Directory: {settings.paths.base_dir}")
    print(f"Config file location: {Path.cwd() / 'config.yaml'}")
    print(f".env file location: {BASE_DIR / '.env'}")
    print(f"Vector Store Directory: {settings.paths.vector_store_dir}")
    print(f"Vector Store Provider: {settings.vector_store.provider}")


    print("=" * 50)
    print("Starting SIMBA Application")
    print("=" * 50)
    
    # Project Info
    print(f"Project Name: {settings.project.name}")
    print(f"Version: {settings.project.version}")
    
    # Model Configurations
    print("\nModel Configurations:")
    print(f"LLM Provider: {settings.llm.provider}")
    print(f"LLM Model: {settings.llm.model_name}")
    print(f"Embedding Provider: {settings.embedding.provider}")
    print(f"Embedding Model: {settings.embedding.model_name}")
    print(f"Embedding Device: {settings.embedding.device}")
    
    # Vector Store & Database
    print("\nStorage Configurations:")
    print(f"Vector Store Provider: {settings.vector_store.provider}")
    print(f"Database Provider: {settings.database.provider}")
    
    # Paths
    print("\nPaths:")
    print(f"Base Directory: {settings.paths.base_dir}")
    print(f"Upload Directory: {settings.paths.upload_dir}")
    print(f"Vector Store Directory: {settings.paths.vector_store_dir}")
    
    print("=" * 50)
