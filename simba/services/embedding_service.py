"""Embedding service using FastEmbed."""

from functools import lru_cache

from fastembed import TextEmbedding

from simba.core.config import settings


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
    model = get_embedding_model()

    # FastEmbed returns a generator, convert to list
    embeddings_generator = model.embed(texts)
    embeddings = [embedding.tolist() for embedding in embeddings_generator]

    return embeddings


def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single text.

    Args:
        text: Text string to embed.

    Returns:
        Embedding vector as a list of floats.
    """
    embeddings = get_embeddings([text])
    return embeddings[0]
