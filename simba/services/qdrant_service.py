"""Qdrant vector database service."""

from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from simba.core.config import settings


@lru_cache
def get_qdrant_client() -> QdrantClient:
    """Get cached Qdrant client instance."""
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


def create_collection(collection_name: str) -> None:
    """Create a new Qdrant collection.

    Args:
        collection_name: Name of the collection to create.
    """
    client = get_qdrant_client()

    # Check if collection already exists
    collections = client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=settings.embedding_dimensions,
            distance=Distance.COSINE,
        ),
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
            - vector: list[float] (embedding vector)
            - payload: dict (metadata like document_id, chunk_text, etc.)
    """
    client = get_qdrant_client()

    qdrant_points = [
        PointStruct(
            id=point["id"],
            vector=point["vector"],
            payload=point.get("payload", {}),
        )
        for point in points
    ]

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
