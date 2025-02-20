import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import yaml
from dotenv import load_dotenv
import logging
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

logger = logging.getLogger(__name__)


class ProjectConfig(BaseModel):
    name: str = "Simba"
    version: str = "1.0.0"
    api_version: str = "/api/v1"

class PathConfig(BaseModel):
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    markdown_dir: Path = Field(default="markdown")
    faiss_index_dir: Path = Field(default="vector_stores/faiss_index")
    vector_store_dir: Path = Field(default="vector_stores")
    upload_dir: Path = Field(default="uploads")

    def __init__(self, **data):
        super().__init__(**data)
        # Make sure all paths are relative to base_dir
        self.markdown_dir = self.base_dir / self.markdown_dir
        self.faiss_index_dir = self.base_dir / self.faiss_index_dir
        self.vector_store_dir = self.base_dir / self.vector_store_dir
        self.upload_dir = self.base_dir / self.upload_dir
        
        # Create directories if they don't exist
        for path in [self.markdown_dir, self.faiss_index_dir, self.vector_store_dir, self.upload_dir]:
            path.mkdir(parents=True, exist_ok=True)

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

class FeaturesConfig(BaseModel):
    enable_parsers: bool = True

class Settings(BaseSettings):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Add features config
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    
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
        if values.data.get('features', FeaturesConfig()).enable_parsers:
            if not v.broker_url:
                raise ValueError("Celery broker URL required when parsers are enabled")
        return v

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> 'Settings':
        """Load settings from config.yaml file with fallback to defaults."""
        # Set base_dir first
        base_dir = Path(__file__).resolve().parent.parent
        
        # If no config path provided, use default
        if config_path is None:
            config_path = base_dir / 'config.yaml'

        # Load YAML configuration
        config_data = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_path}")
                
                # Handle the embedding/embeddings field name difference
                if 'embedding' in config_data:
                    config_data['embedding'] = config_data['embedding']
                
                logger.debug(f"Configuration data: {config_data}")
        else:
            logger.warning(f"No configuration file found at {config_path}, using defaults")
        
        # Ensure paths.base_dir is set
        if 'paths' in config_data:
            config_data['paths']['base_dir'] = str(base_dir)
        
        # Create settings instance with YAML data
        settings = cls(**config_data)
        
        # Set derived paths
        settings.paths.base_dir = base_dir
        settings.paths.markdown_dir = settings.paths.base_dir / settings.paths.markdown_dir
        settings.paths.faiss_index_dir = settings.paths.base_dir / settings.paths.faiss_index_dir
        settings.paths.vector_store_dir = settings.paths.base_dir / settings.paths.vector_store_dir
        settings.paths.upload_dir = settings.paths.base_dir / settings.paths.upload_dir

        return settings

# Create global settings instance
try:
    settings = Settings.load_from_yaml()
except Exception as e:
    print(f"Warning: Failed to load configuration file, using defaults: {e}")
    settings = Settings()

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        settings.paths.markdown_dir,
        settings.paths.faiss_index_dir,
        settings.paths.vector_store_dir
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# Create directories on import
ensure_directories()

if __name__ == "__main__":
    print("\nCurrent Settings:")
    print(f"Base Directory: {settings.paths.base_dir}")
    print(f"Vector Store Provider: {settings.vector_store.provider}")
    print(f"Embedding Model: {settings.embedding.model_name}")
