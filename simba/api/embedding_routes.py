from typing import List

from fastapi import APIRouter, HTTPException

from simba.embeddings import EmbeddingService

embedding_route = APIRouter()

# Initialize the embedding service
embedding_service = EmbeddingService()


@embedding_route.post("/embed/documents")
async def embed_documents():
    """Embed all documents in the database into the vector store."""
    try:
        langchain_documents = embedding_service.embed_all_documents()
        return langchain_documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@embedding_route.post("/embed/document")
async def embed_document(doc_id: str):
    """Embed a specific document into the vector store."""
    try:
        langchain_documents = embedding_service.embed_document(doc_id)
        return langchain_documents
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@embedding_route.get("/embedded_documents")
async def get_embedded_documents():
    """Get all documents from the vector store."""
    try:
        docs = embedding_service.get_embedded_documents()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@embedding_route.delete("/embed/document/chunk")
async def delete_document_chunk(chunk_ids: List[str]):
    """Delete a list of document chunks from the vector store."""
    try:
        result = embedding_service.delete_document_chunks(chunk_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@embedding_route.delete("/embed/document")
async def delete_document(doc_id: str):
    """Delete all chunks of a document from the vector store."""
    try:
        result = embedding_service.delete_document(doc_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@embedding_route.delete("/embed/clear_store")
async def clear_store():
    """Clear the entire vector store."""
    try:
        result = embedding_service.clear_store()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
