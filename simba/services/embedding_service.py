"""Embedding service using FastEmbed."""

import logging
from functools import lru_cache

from cachetools import TTLCache
from fastembed import SparseTextEmbedding, TextEmbedding

from simba.core.config import settings
from simba.services.metrics_service import EMBEDDING_LATENCY, track_latency

logger = logging.getLogger(__name__)

# TTL cache for query embeddings (5 min TTL, max 1000 entries)
_embedding_cache: TTLCache = TTLCache(maxsize=1000, ttl=300)
_sparse_embedding_cache: TTLCache = TTLCache(maxsize=1000, ttl=300)


@lru_cache
def get_embedding_model() -> TextEmbedding:
    """Get cached FastEmbed model instance.

    The model is downloaded and cached on first use.
    """
    return TextEmbedding(model_name=settings.embedding_model)


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each vector is a list of floats).
    """
    with track_latency(EMBEDDING_LATENCY):
        model = get_embedding_model()

        # FastEmbed returns a generator, convert to list
        embeddings_generator = model.embed(texts)
        embeddings = [embedding.tolist() for embedding in embeddings_generator]

    return embeddings


def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single text.

    Uses TTL cache to avoid recomputing embeddings for repeated queries.

    Args:
        text: Text string to embed.

    Returns:
        Embedding vector as a list of floats.
    """
    # Check cache first
    if text in _embedding_cache:
        return _embedding_cache[text]

    # Generate and cache
    embeddings = get_embeddings([text])
    embedding = embeddings[0]
    _embedding_cache[text] = embedding

    return embedding


# --- Sparse Embeddings (SPLADE) ---


@lru_cache
def get_sparse_embedding_model() -> SparseTextEmbedding:
    """Get cached sparse embedding model instance (SPLADE).

    The model is downloaded and cached on first use.
    """
    logger.info(f"Loading sparse embedding model: {settings.retrieval_sparse_model}")
    return SparseTextEmbedding(model_name=settings.retrieval_sparse_model)


def get_sparse_embeddings(texts: list[str]) -> list[tuple[list[int], list[float]]]:
    """Generate sparse embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of (indices, values) tuples for sparse vectors.
    """
    model = get_sparse_embedding_model()

    # SparseTextEmbedding returns a generator of SparseEmbedding objects
    embeddings_generator = model.embed(texts)
    results = []

    for sparse_embedding in embeddings_generator:
        # SparseEmbedding has .indices and .values attributes
        results.append(
            (
                sparse_embedding.indices.tolist(),
                sparse_embedding.values.tolist(),
            )
        )

    return results


def get_sparse_embedding(text: str) -> tuple[list[int], list[float]]:
    """Generate sparse embedding for a single text.

    Uses TTL cache to avoid recomputing embeddings for repeated queries.

    Args:
        text: Text string to embed.

    Returns:
        Tuple of (indices, values) for sparse vector.
    """
    # Check cache first
    if text in _sparse_embedding_cache:
        return _sparse_embedding_cache[text]

    # Generate and cache
    embeddings = get_sparse_embeddings([text])
    embedding = embeddings[0]
    _sparse_embedding_cache[text] = embedding

    return embedding
