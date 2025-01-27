from core.factories.database_factory import get_database
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Body
from fastapi.responses import JSONResponse
import base64
import os
from pathlib import Path
import uuid
from datetime import datetime
import asyncio

from typing import List, Optional, cast
from services.ingestion_service.config import SUPPORTED_EXTENSIONS
from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from services.ingestion_service.file_handling import load_file_from_path, save_file_locally
from services.ingestion_service.types import  SimbaDoc
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
db = get_database()

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

@ingestion.get("/ingestion")
async def get_ingestion_documents():
    """Get all ingested documents grouped by folder"""
    return db.get_all_documents()

@ingestion.get("/ingestion/{uid}")
async def get_document(uid: str):
    """Get a document by ID"""
    return db.get_document(uid)


@ingestion.delete("/ingestion")
async def delete_document(uids: List[str]):
    """Delete a document by ID"""
    db.delete_documents(uids)
    return {"message": f"Documents {uids} deleted successfully"}


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


