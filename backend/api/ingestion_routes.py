from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import base64
import os
from pathlib import Path
import uuid
from datetime import datetime

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

# Document Management Routes
# ------------------------

@ingestion.post("/ingestion")
async def ingest_document(
    file: UploadFile = File(...),
    folder_path: str = Query(default="/", description="Folder path to store the document")
):
    """Ingest a document into the vector store"""
    try:
        store_path = Path(settings.paths.upload_dir)
        if folder_path != "/":
            store_path = store_path / folder_path.strip("/")

        #we store the file in the folder
        save_file_locally(file, store_path)
        
        ingestion_service = DocumentIngestionService()
        return ingestion_service.ingest_document(file, folder_path=store_path)
    except Exception as e:
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

# Folder Management Routes
# -----------------------

@ingestion.post("/folders")
async def create_folder_endpoint(folder: FolderCreate) -> Folder:
    """Create a new folder"""
    return create_folder(folder.name, folder.parent_path)

@ingestion.get("/folders")
async def get_folders_endpoint() -> List[Folder]:
    """Get all folders"""
    return get_folders()

@ingestion.delete("/folders/{folder_id}")
async def delete_folder_endpoint(folder_id: str) -> dict:
    """Delete a folder"""
    delete_folder(folder_id)
    return {"message": f"Folder {folder_id} deleted successfully"}

@ingestion.post("/folders/move")
async def move_to_folder_endpoint(move: FolderMove) -> dict:
    """Move a document to a folder"""
    try:
        ingestion_service = DocumentIngestionService()
        document = ingestion_service.get_document(move.document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {move.document_id} not found")
        
        new_path = move_to_folder(document.metadata['file_path'], move.folder_id)
        
        # Update document metadata and vector store
        document.metadata.update({
            'file_path': new_path,
            'folder_id': move.folder_id
        })
        VectorStoreService().update_document(document)
        
        return {"message": "Document moved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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


