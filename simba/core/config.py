"""Application configuration."""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env into actual environment variables (required for init_chat_model)
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Simba"
    app_version: str = "0.5.0"
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "postgresql://simba:simba@localhost:5432/simba"

    # LLM (provider-agnostic via init_chat_model)
    # Format: "provider:model" e.g. "openai:gpt-4o-mini", "anthropic:claude-3-opus"
    llm_model: str = "openai:gpt-4o-mini"
    llm_temperature: float = 0.1

    # LLM Reasoning (for models that support it: o1, o3, claude with thinking, etc.)
    # Values: None (disabled), "low", "medium", "high"
    llm_reasoning_effort: str | None = None
    # Anthropic thinking budget (only used when provider is anthropic and reasoning is enabled)
    llm_thinking_budget: int = 10000

    # Embedding (FastEmbed - local, free, fast)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 384

    # Retrieval settings
    retrieval_min_score: float = 0.7
    retrieval_limit: int = 5
    retrieval_rerank: bool = True
    retrieval_hybrid: bool = True
    retrieval_sparse_model: str = "prithvida/Splade_PP_en_v1"

    # Reranker settings
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_top_k: int = 5

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None

    # MinIO (S3-compatible storage)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "simba-documents"
    minio_secure: bool = False

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Document parsing
    # Options: "docling", "mistral", "unstructured"
    parser_backend: str = "docling"
    mistral_api_key: str | None = None
    unstructured_api_key: str | None = None
    unstructured_api_url: str = "https://api.unstructuredapp.io/general/v0/general"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
