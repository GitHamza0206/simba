"""Qdrant vector database service."""

import logging
from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    MatchValue,
    PointStruct,
    Prefetch,
    SparseIndexParams,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from simba.core.config import settings
from simba.services.metrics_service import SEARCH_LATENCY, track_latency

logger = logging.getLogger(__name__)


@lru_cache
def get_qdrant_client() -> QdrantClient:
    """Get cached Qdrant client instance."""
    host = settings.qdrant_host

    # If host contains a protocol, use url parameter instead
    if host.startswith("http://") or host.startswith("https://"):
        return QdrantClient(
            url=host,
            api_key=settings.qdrant_api_key,
        )

    # Local connection without protocol
    return QdrantClient(
        host=host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
    )


def create_collection(collection_name: str, with_sparse: bool = True) -> None:
    """Create a new Qdrant collection with optional sparse vector support.

    Args:
        collection_name: Name of the collection to create.
        with_sparse: Whether to include sparse vector configuration for hybrid search.
    """
    client = get_qdrant_client()

    # Check if collection already exists
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        return

    sparse_config = None
    if with_sparse:
        sparse_config = {"text-sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))}

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=settings.embedding_dimensions,
            distance=Distance.COSINE,
        ),
        sparse_vectors_config=sparse_config,
    )


def delete_collection(collection_name: str) -> None:
    """Delete a Qdrant collection.

    Args:
        collection_name: Name of the collection to delete.
    """
    client = get_qdrant_client()
    client.delete_collection(collection_name=collection_name)


def collection_exists(collection_name: str) -> bool:
    """Check if a collection exists.

    Args:
        collection_name: Name of the collection.

    Returns:
        True if collection exists, False otherwise.
    """
    client = get_qdrant_client()
    collections = client.get_collections().collections
    return any(c.name == collection_name for c in collections)


def upsert_vectors(
    collection_name: str,
    points: list[dict[str, Any]],
) -> None:
    """Insert or update vectors in a collection.

    Args:
        collection_name: Name of the collection.
        points: List of points with id, vector, and payload.
            Each point should have:
            - id: str (unique identifier)
            - vector: list[float] (dense embedding vector)
            - sparse_indices: list[int] (optional, sparse vector indices)
            - sparse_values: list[float] (optional, sparse vector values)
            - payload: dict (metadata like document_id, chunk_text, etc.)
    """
    client = get_qdrant_client()

    qdrant_points = []
    for point in points:
        # Build vector config - can be just dense or dense + sparse
        has_sparse = "sparse_indices" in point and "sparse_values" in point

        if has_sparse:
            vector = {
                "": point["vector"],  # Default dense vector
                "text-sparse": SparseVector(
                    indices=point["sparse_indices"],
                    values=point["sparse_values"],
                ),
            }
        else:
            vector = point["vector"]

        qdrant_points.append(
            PointStruct(
                id=point["id"],
                vector=vector,
                payload=point.get("payload", {}),
            )
        )

    client.upsert(
        collection_name=collection_name,
        points=qdrant_points,
    )


def search(
    collection_name: str,
    query_vector: list[float],
    limit: int = 5,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    """Search for similar vectors in a collection.

    Args:
        collection_name: Name of the collection.
        query_vector: Query embedding vector.
        limit: Maximum number of results.
        document_id: Optional filter by document ID.

    Returns:
        List of search results with id, score, and payload.
    """
    client = get_qdrant_client()

    query_filter = None
    if document_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    with track_latency(SEARCH_LATENCY):
        results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points

    return [
        {
            "id": result.id,
            "score": result.score,
            "payload": result.payload,
        }
        for result in results
    ]


def collection_has_sparse_vectors(collection_name: str) -> bool:
    """Check if a collection has sparse vector configuration.

    Args:
        collection_name: Name of the collection.

    Returns:
        True if collection supports sparse vectors, False otherwise.
    """
    client = get_qdrant_client()
    try:
        info = client.get_collection(collection_name=collection_name)
        # Check if sparse_vectors_config exists and has 'text-sparse'
        sparse_config = info.config.params.sparse_vectors
        return sparse_config is not None and "text-sparse" in sparse_config
    except Exception:
        return False


def hybrid_search(
    collection_name: str,
    query_dense: list[float],
    query_sparse: tuple[list[int], list[float]] | None = None,
    limit: int = 5,
    document_id: str | None = None,
) -> list[dict[str, Any]]:
    """Hybrid search using dense + sparse vectors with RRF fusion.

    Falls back to dense-only search if collection doesn't support sparse vectors
    or if sparse query is not provided.

    Args:
        collection_name: Name of the collection.
        query_dense: Dense embedding vector.
        query_sparse: Optional tuple of (indices, values) for sparse vector.
        limit: Maximum number of results.
        document_id: Optional filter by document ID.

    Returns:
        List of search results with id, score, and payload.
    """
    client = get_qdrant_client()

    # Build filter if document_id specified
    query_filter = None
    if document_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    # Check if we can do hybrid search
    has_sparse = collection_has_sparse_vectors(collection_name)

    if not has_sparse or query_sparse is None:
        if query_sparse is not None and not has_sparse:
            logger.warning(
                f"Collection '{collection_name}' does not support sparse vectors. "
                "Falling back to dense-only search. Consider re-indexing with sparse vectors."
            )
        # Fall back to dense-only search
        return search(collection_name, query_dense, limit, document_id)

    with track_latency(SEARCH_LATENCY):
        # Hybrid search with RRF fusion
        results = client.query_points(
            collection_name=collection_name,
            prefetch=[
                Prefetch(
                    query=query_dense,
                    using="",  # Default dense vector
                    limit=limit * 2,
                    filter=query_filter,
                ),
                Prefetch(
                    query=SparseVector(
                        indices=query_sparse[0],
                        values=query_sparse[1],
                    ),
                    using="text-sparse",
                    limit=limit * 2,
                    filter=query_filter,
                ),
            ],
            query=Fusion.RRF,
            limit=limit,
            with_payload=True,
        ).points

    return [
        {
            "id": result.id,
            "score": result.score,
            "payload": result.payload,
        }
        for result in results
    ]


def delete_by_document_id(collection_name: str, document_id: str) -> None:
    """Delete all vectors associated with a document.

    Args:
        collection_name: Name of the collection.
        document_id: Document ID to delete vectors for.
    """
    client = get_qdrant_client()

    client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )


def get_collection_info(collection_name: str) -> dict[str, Any]:
    """Get information about a collection.

    Args:
        collection_name: Name of the collection.

    Returns:
        Collection information including point count.
    """
    client = get_qdrant_client()
    info = client.get_collection(collection_name=collection_name)

    return {
        "name": collection_name,
        "points_count": info.points_count,
        "vectors_count": info.vectors_count,
        "status": info.status.value,
    }


def get_document_chunks(
    collection_name: str,
    document_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get all chunks for a specific document.

    Args:
        collection_name: Name of the collection.
        document_id: Document ID to get chunks for.
        limit: Maximum number of chunks to return.

    Returns:
        List of chunks with their payload (text, position, etc.).
    """
    client = get_qdrant_client()

    # Use scroll to get all points matching the document_id
    results, _ = client.scroll(
        collection_name=collection_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    # Sort by chunk_position and return
    chunks = [
        {
            "id": str(point.id),
            "text": point.payload.get("chunk_text", ""),
            "position": point.payload.get("chunk_position", 0),
            "document_name": point.payload.get("document_name", ""),
        }
        for point in results
    ]

    return sorted(chunks, key=lambda x: x["position"])
