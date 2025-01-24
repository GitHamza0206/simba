from typing import List
from fastapi import APIRouter, HTTPException
from services.splitter import split_document
from services.vector_store_service import VectorStoreService

embedding_route = APIRouter()

@embedding_route.post('/embed/documents')
async def embed_documents(documents_ids: List[str]):
    try:    
        store = VectorStoreService()
        documents_to_index = [store.get_document(document_id) for document_id in documents_ids]
        chunks = split_document(documents_to_index)
        store.add_documents(chunks)
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    