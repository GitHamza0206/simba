import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import yaml
from dotenv import load_dotenv

load_dotenv()


class ProjectConfig(BaseModel):
    name: str = "MigiBot"
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
    # Get API key from environment variable
    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key from environment variables"
    )
    temperature: float = Field(default=0.0)
    streaming: bool = Field(default=True)
    max_tokens: Optional[int] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  

    provider: str = "openai"
    model_name: str = "text-embedding-3-small"
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class VectorStoreConfig(BaseModel):
    provider: str = "faiss"
    collection_name: str = "migi_collection"
    additional_params: Dict[str, Any] = Field(default_factory=dict)

class ChunkingConfig(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 50

class Settings(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> 'Settings':
        """Load settings from config.yaml file with fallback to defaults."""
        # Set base_dir first
        base_dir = Path(__file__).resolve().parent.parent
        
        # Start with default settings
        settings = cls()
        settings.paths.base_dir = base_dir  # Ensure base_dir is set
        
        # If no config path provided, use default
        if config_path is None:
            config_path = base_dir / 'config.yaml'

        # If config file exists, update defaults with file values
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
                
            # Ensure paths.base_dir is set before updating
            if 'paths' in config_data:
                config_data['paths']['base_dir'] = str(base_dir)
            
            # Update settings with YAML data
            settings_dict = settings.model_dump()
            cls._deep_update(settings_dict, config_data)
            settings = cls(**settings_dict)

        # Set derived paths
        settings.paths.markdown_dir = settings.paths.base_dir / settings.paths.markdown_dir
        settings.paths.faiss_index_dir = settings.paths.base_dir / settings.paths.faiss_index_dir
        settings.paths.vector_store_dir = settings.paths.base_dir / settings.paths.vector_store_dir

        return settings

    @staticmethod
    def _deep_update(dict1: dict, dict2: dict) -> None:
        """Deep update dictionary, preserving nested structures."""
        for k, v in dict2.items():
            if k in dict1 and isinstance(dict1[k], dict) and isinstance(v, dict):
                Settings._deep_update(dict1[k], v)
            else:
                dict1[k] = v

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
