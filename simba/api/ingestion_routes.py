import asyncio
import base64
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, cast

from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from langchain_core.documents import Document
from simba.models.simbadoc import SimbaDoc
from pydantic import BaseModel

from simba.ingestion.document_ingestion import DocumentIngestionService
from simba.ingestion.file_handling import save_file_locally
from simba.ingestion.utils import check_file_exists
from simba.ingestion import Loader


logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

ingestion = APIRouter()

ingestion_service = DocumentIngestionService()
db = get_database()
loader = Loader()
kms = DocumentIngestionService()
store = VectorStoreFactory.get_vector_store()

# Document Management Routes
# ------------------------

@ingestion.post("/ingestion")
async def ingest_document(
    files: List[UploadFile] = File(...),
    folder_path: str = Query(default="/", description="Folder path to store the document")
):
    """Ingest a document into the vector store"""
    try:
        store_path = Path(settings.paths.upload_dir)
        if folder_path != "/":
            store_path = store_path / folder_path.strip("/")

        # Process files concurrently using asyncio.gather
        async def process_file(file):
            await file.seek(0)
            await save_file_locally(file, store_path)
            await file.seek(0)
            simba_doc = await ingestion_service.ingest_document(file)
            return simba_doc

        # Process all files concurrently
        response = await asyncio.gather(*[process_file(file) for file in files])
        # Insert into database
        db.insert_documents(response)
        return response

    except Exception as e:
        logger.error(f"Error in ingest_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@ingestion.put("/ingestion/update_document")
async def update_document(doc_id: str, new_simbadoc: SimbaDoc):
    """Update a document"""
    try:    
        
        # Update the document in the database
        success = db.update_document(doc_id, new_simbadoc)
        if not success:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        return new_simbadoc
    except Exception as e:
        logger.error(f"Error in update_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@ingestion.get("/ingestion")
async def get_ingestion_documents():
    """Get all ingested documents"""
    # Ensure database is in a fresh state
    documents = db.get_all_documents()
    return documents

@ingestion.get("/ingestion/{uid}")
async def get_document(uid: str):
    """Get a document by ID"""
    # Ensure database is in a fresh state
    document = db.get_document(uid)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {uid} not found")
    return document


@ingestion.delete("/ingestion")
async def delete_document(uids: List[str]):
    """Delete a document by ID"""
    try:    
        # Delete documents from vector store
        for uid in uids:
            simbadoc = db.get_document(uid)
            if simbadoc.metadata.enabled:
                store.delete_documents([doc.id for doc in simbadoc.documents])
                
        # Delete documents from database
        db.delete_documents(uids)

        #kms.sync_with_store()
        return {"message": f"Documents {uids} deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Routes
# -------------

@ingestion.get("/loaders")
async def get_loaders():
    """Get supported document loaders"""
    return {"loaders": [l.__name__ for l in loader.SUPPORTED_EXTENSIONS.values()]}

@ingestion.get("/parsers")
async def get_parsers():
    """Get supported parsers"""
    return {"parsers": "docling"}

@ingestion.get("/upload-directory")
async def get_upload_directory():
    """Get upload directory path"""
    return {"path": str(settings.paths.upload_dir)}


