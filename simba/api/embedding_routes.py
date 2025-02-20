from typing import List, cast

from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from fastapi import APIRouter, HTTPException
from simba.models.simbadoc import SimbaDoc
from simba.ingestion.document_ingestion import (
    DocumentIngestionService,
)
from simba.splitting import Splitter

embedding_route = APIRouter()

db = get_database()
store = VectorStoreFactory.get_vector_store()
splitter = Splitter()
kms = DocumentIngestionService()

@embedding_route.post('/embed/documents')
async def embed_documents():
    try:    
        all_documents = db.get_all_documents()
        simba_documents = [cast(SimbaDoc, doc) for doc in all_documents]
        # to Langchain documents
        langchain_documents = [doc for simbadoc in simba_documents for doc in simbadoc.documents]
        store.add_documents(langchain_documents)
        # Update enabled status for each document
        for doc in simba_documents:
            doc.metadata.enabled = True
            db.update_document(doc.id, doc)
        return langchain_documents

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@embedding_route.post('/embed/document')
async def embed_document(doc_id: str):
    try:
        simbadoc: SimbaDoc = db.get_document(doc_id)
        langchain_documents = simbadoc.documents

        try:
            store.add_documents(langchain_documents)
            simbadoc.metadata.enabled = True
            db.update_document(doc_id, simbadoc)
            #kms.sync_with_store()

        except ValueError as ve:
            # If the error is about existing IDs, consider it a success
            if "Tried to add ids that already exist" in str(ve):
                return langchain_documents  # Return success response
            raise ve  # Re-raise if it's a different ValueError
        
        return langchain_documents

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@embedding_route.get('/embedded_documents')
async def get_embedded_documents():
    try:
        docs = store.get_documents()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@embedding_route.delete('/embed/document/chunk')
async def delete_document_chunk(chunk_ids: List[str]):
    """Delete a list of document chunks"""
    try:
        store.delete_documents(chunk_ids)

        return {"message": "Document chunk deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@embedding_route.delete('/embed/document')
async def delete_document(doc_id: str):
    """Delete a list of documents"""
    try:
        simbadoc: SimbaDoc = db.get_document(doc_id)
        docs_ids = [doc.id for doc in simbadoc.documents]
        store.delete_documents(docs_ids)
        simbadoc.metadata.enabled = False
        db.update_document(doc_id, simbadoc)
        #kms.sync_with_store()  
        
        return {"message": "Documents deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@embedding_route.delete("/embed/clear_store")
async def clear_store():
    store.clear_store()
    #kms.sync_with_store()
    return {"message": "Store cleared"}