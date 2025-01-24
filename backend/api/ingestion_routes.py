from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import base64
import os
from pathlib import Path
import uuid
from datetime import datetime
import asyncio

from typing import List, Optional
from services.ingestion_service.config import SUPPORTED_EXTENSIONS
from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from services.ingestion_service.file_handling import load_file_from_path, save_file_locally
from services.ingestion_service.types import IngestedDocument
from services.ingestion_service.utils import check_file_exists
from services.parser_service import ParserService
from services.vector_store_service import VectorStoreService
from core.config import settings

from langchain_core.documents import Document
import logging

from pydantic import BaseModel
from services.ingestion_service.folder_handling import (
    create_folder,
    get_folders,
    delete_folder,
    move_to_folder,
    FolderCreate,
    FolderMove,
    Folder
)

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

ingestion = APIRouter()

ingestion_service = DocumentIngestionService()

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
        ingestion_service.database.insert_documents(response)
        return response

    except Exception as e:
        logger.error(f"Error in ingest_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@ingestion.get("/ingestion")
async def get_ingestion_documents():
    """Get all ingested documents grouped by folder"""
    ingestion_service = DocumentIngestionService()
    return ingestion_service.get_ingested_documents_by_folder()

@ingestion.delete("/ingestion")
async def delete_ingestion_documents(uid: str) -> dict:
    """Delete a document by ID"""
    ingestion_service = DocumentIngestionService()
    ingestion_service.delete_ingested_document(uid, delete_locally=True)
    return {"message": f"Document {uid} deleted successfully"}



# Document Processing Routes
# ------------------------

@ingestion.get("/document/{document_id}")
async def get_document_content(document_id: str):
    """Get document content by ID"""
    try:
        document = VectorStoreService().get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ingestion.put("/document/{document_id}")
async def update_document(document_id: str, newDocument: Document):
    """Update document content"""
    ingestion_service = DocumentIngestionService()
    ingestion_service.update_document(document_id, newDocument)
    return {"message": f"Document {document_id} updated successfully"}

@ingestion.post("/ingestion/reindex")
async def reindex_document(document_id: str, parser: str):
    """Reindex a document with a new parser"""
    try:
        vector_store = VectorStoreService()
        document = vector_store.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        parsed_document = ParserService().parse_document(document, parser)
        if not vector_store.update_document(document_id, parsed_document):
            raise HTTPException(status_code=500, detail="Failed to reindex document")
        
        return parsed_document
    except Exception as e:
        logger.error(f"Reindexing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility Routes
# -------------

@ingestion.get("/loaders")
async def get_loaders():
    """Get supported document loaders"""
    return {"loaders": [loader.__name__ for loader in SUPPORTED_EXTENSIONS.values()]}

@ingestion.get("/parsers")
async def get_parsers():
    """Get supported parsers"""
    return {"parsers": ParserService().get_parsers()}

@ingestion.get("/upload-directory")
async def get_upload_directory():
    """Get upload directory path"""
    return {"path": str(settings.paths.upload_dir)}


