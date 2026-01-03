"""Reranker service using cross-encoder models."""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from simba.core.config import settings
from simba.services.metrics_service import track_latency, RERANK_LATENCY

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from simba.services.retrieval_service import RetrievedChunk


@lru_cache
def get_reranker():
    """Get cached cross-encoder reranker model.

    Uses sentence-transformers CrossEncoder with a configurable model.
    """
    from sentence_transformers import CrossEncoder

    logger.info(f"Loading reranker model: {settings.reranker_model}")
    return CrossEncoder(settings.reranker_model)


def rerank_chunks(
    query: str,
    chunks: list["RetrievedChunk"],
    top_k: int | None = None,
) -> list["RetrievedChunk"]:
    """Rerank chunks using cross-encoder model.

    Args:
        query: The search query.
        chunks: List of chunks to rerank.
        top_k: Number of top results to return. Defaults to settings.reranker_top_k.

    Returns:
        Reranked list of chunks, sorted by relevance.
    """
    if not chunks:
        return []

    top_k = top_k if top_k is not None else settings.reranker_top_k

    with track_latency(RERANK_LATENCY):
        reranker = get_reranker()

        # Prepare query-document pairs for cross-encoder
        pairs = [(query, chunk.chunk_text) for chunk in chunks]

        # Get cross-encoder scores
        scores = reranker.predict(pairs)

        # Combine chunks with new scores and sort
        scored_chunks = list(zip(chunks, scores))
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Update scores and return top_k
        result = []
        for chunk, score in scored_chunks[:top_k]:
            # Create new chunk with updated score
            from simba.services.retrieval_service import RetrievedChunk

            result.append(
                RetrievedChunk(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    chunk_text=chunk.chunk_text,
                    chunk_position=chunk.chunk_position,
                    score=float(score),
                )
            )

    return result
