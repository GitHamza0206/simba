"""Retrieval service for RAG queries."""

import time
from dataclasses import dataclass
from typing import TypedDict

from qdrant_client.http.exceptions import UnexpectedResponse

from simba.core.config import settings
from simba.services import embedding_service, qdrant_service
from simba.services.metrics_service import track_latency, RETRIEVAL_LATENCY


class LatencyBreakdown(TypedDict, total=False):
    """Latency breakdown for retrieval operations."""

    embedding_ms: float
    sparse_embedding_ms: float
    search_ms: float
    rerank_ms: float
    total_ms: float


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk from the vector store."""

    document_id: str
    document_name: str
    chunk_text: str
    chunk_position: int
    score: float


def retrieve(
    query: str,
    collection_name: str,
    limit: int | None = None,
    min_score: float | None = None,
    rerank: bool | None = None,
    hybrid: bool | None = None,
    return_latency: bool = False,
) -> list[RetrievedChunk] | tuple[list[RetrievedChunk], LatencyBreakdown]:
    """Retrieve relevant chunks for a query.

    Args:
        query: The search query.
        collection_name: Name of the collection to search.
        limit: Maximum number of results. Defaults to settings.retrieval_limit.
        min_score: Minimum similarity score threshold. Defaults to settings.retrieval_min_score.
        rerank: Whether to apply cross-encoder reranking. Defaults to settings.retrieval_rerank.
        hybrid: Whether to use hybrid search (dense + sparse). Defaults to settings.retrieval_hybrid.
        return_latency: Whether to return latency breakdown.

    Returns:
        List of retrieved chunks sorted by relevance.
        If return_latency=True, returns tuple of (chunks, latency_breakdown).
    """
    # Use config defaults if not specified
    limit = limit if limit is not None else settings.retrieval_limit
    min_score = min_score if min_score is not None else settings.retrieval_min_score
    rerank = rerank if rerank is not None else settings.retrieval_rerank
    hybrid = hybrid if hybrid is not None else settings.retrieval_hybrid

    latency: LatencyBreakdown = {}
    total_start = time.perf_counter()

    with track_latency(RETRIEVAL_LATENCY):
        # Generate dense query embedding
        embed_start = time.perf_counter()
        query_dense = embedding_service.get_embedding(query)
        latency["embedding_ms"] = (time.perf_counter() - embed_start) * 1000

        # Generate sparse query embedding if hybrid search enabled
        query_sparse = None
        if hybrid:
            sparse_start = time.perf_counter()
            query_sparse = embedding_service.get_sparse_embedding(query)
            latency["sparse_embedding_ms"] = (time.perf_counter() - sparse_start) * 1000

        # Search Qdrant - fetch more results if reranking
        search_limit = limit * 4 if rerank else limit

        search_start = time.perf_counter()
        try:
            if hybrid:
                results = qdrant_service.hybrid_search(
                    collection_name=collection_name,
                    query_dense=query_dense,
                    query_sparse=query_sparse,
                    limit=search_limit,
                )
            else:
                results = qdrant_service.search(
                    collection_name=collection_name,
                    query_vector=query_dense,
                    limit=search_limit,
                )
        except UnexpectedResponse:
            # Collection doesn't exist
            if return_latency:
                latency["search_ms"] = (time.perf_counter() - search_start) * 1000
                latency["total_ms"] = (time.perf_counter() - total_start) * 1000
                return [], latency
            return []
        latency["search_ms"] = (time.perf_counter() - search_start) * 1000

        # Filter by minimum score and convert to RetrievedChunk objects
        chunks = []
        for result in results:
            if result["score"] >= min_score:
                payload = result["payload"]
                chunks.append(
                    RetrievedChunk(
                        document_id=payload.get("document_id", ""),
                        document_name=payload.get("document_name", ""),
                        chunk_text=payload.get("chunk_text", ""),
                        chunk_position=payload.get("chunk_position", 0),
                        score=result["score"],
                    )
                )

        # Apply reranking if enabled
        if rerank and chunks:
            from simba.services.reranker_service import rerank_chunks

            rerank_start = time.perf_counter()
            chunks = rerank_chunks(query, chunks, top_k=limit)
            latency["rerank_ms"] = (time.perf_counter() - rerank_start) * 1000
        elif rerank:
            # No chunks to rerank, just return empty
            pass
        else:
            # No reranking, truncate to limit
            chunks = chunks[:limit]

    latency["total_ms"] = (time.perf_counter() - total_start) * 1000

    if return_latency:
        return chunks, latency
    return chunks


def retrieve_formatted(
    query: str,
    collection_name: str,
    limit: int | None = None,
    return_latency: bool = False,
) -> str | tuple[str, LatencyBreakdown]:
    """Retrieve and format chunks as context for LLM.

    Args:
        query: The search query.
        collection_name: Name of the collection to search.
        limit: Maximum number of results. Defaults to settings.retrieval_limit.
        return_latency: Whether to return latency breakdown.

    Returns:
        Formatted string with retrieved context.
        If return_latency=True, returns tuple of (formatted_context, latency_breakdown).
    """
    result = retrieve(query, collection_name, limit=limit, return_latency=return_latency)

    if return_latency:
        chunks, latency = result
    else:
        chunks = result
        latency = {}

    if not chunks:
        output = "No relevant information found in the knowledge base."
        if return_latency:
            return output, latency
        return output

    # Format chunks as context
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk.document_name}]\n{chunk.chunk_text}"
        )

    output = "\n\n---\n\n".join(context_parts)

    if return_latency:
        return output, latency
    return output
