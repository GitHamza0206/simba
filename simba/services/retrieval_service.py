"""Retrieval service for RAG queries."""

from dataclasses import dataclass

from simba.services import embedding_service, qdrant_service


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
    limit: int = 5,
    min_score: float = 0.0,
) -> list[RetrievedChunk]:
    """Retrieve relevant chunks for a query.

    Args:
        query: The search query.
        collection_name: Name of the collection to search.
        limit: Maximum number of results.
        min_score: Minimum similarity score threshold.

    Returns:
        List of retrieved chunks sorted by relevance.
    """
    # Check if collection exists
    if not qdrant_service.collection_exists(collection_name):
        return []

    # Generate query embedding
    query_embedding = embedding_service.get_embedding(query)

    # Search Qdrant
    results = qdrant_service.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=limit,
    )

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

    return chunks


def retrieve_formatted(
    query: str,
    collection_name: str,
    limit: int = 5,
) -> str:
    """Retrieve and format chunks as context for LLM.

    Args:
        query: The search query.
        collection_name: Name of the collection to search.
        limit: Maximum number of results.

    Returns:
        Formatted string with retrieved context.
    """
    chunks = retrieve(query, collection_name, limit)

    if not chunks:
        return "No relevant information found in the knowledge base."

    # Format chunks as context
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk.document_name}]\n{chunk.chunk_text}"
        )

    return "\n\n---\n\n".join(context_parts)
