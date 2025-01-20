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
from services.ingestion_service.file_handling import load_file_from_path
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



@ingestion.delete("/ingestion")
async def delete_ingestion_documents(uid: str)->dict :
    ingestion_service = DocumentIngestionService()
    ingestion_service.delete_ingested_document(uid, delete_locally=True)
    return {"message": f"Document {uid} deleted successfully"}

@ingestion.get("/ingestion")
async def get_ingestion_documents():
    ingestion_service = DocumentIngestionService()
    ingested_documents = ingestion_service.get_ingested_documents()
    return ingested_documents

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
            raise HTTPException(
                status_code=404,
                detail=f"Document {move.document_id} not found"
            )
        
        new_path = move_to_folder(document.metadata['file_path'], move.folder_id)
        
        # Update document metadata
        document.metadata['file_path'] = new_path
        document.metadata['folder_id'] = move.folder_id
        
        # Update the document in the vector store
        vector_store = VectorStoreService()
        vector_store.update_document(document)
        
        return {"message": "Document moved successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error moving document: {str(e)}"
        )

@ingestion.post("/ingestion")
async def ingest_document(
    file: UploadFile = File(...),
    folder_path: str = Query(default="/", description="Folder path to store the document")
):
    """Ingest documents into the vector store with folder support"""
    try:
        # Validate folder path
        upload_dir  = Path(settings.paths.upload_dir)
        store_path = upload_dir
        if folder_path != "/":
            store_path = upload_dir / folder_path.strip("/")

        #check if document already exists
        if check_file_exists(store_path / file.filename):
            return JSONResponse(
                status_code=400,
                content={"message": f"Document {file.filename} already exists in {store_path}"}
            )
        
        ingestion_service = DocumentIngestionService()
        result = ingestion_service.ingest_document(file, folder_path=store_path)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@ingestion.put("/document/{document_id}")
async def update_document(document_id: str, newDocument: Document):
    """Update the loader of a specific document"""
    ingestion_service = DocumentIngestionService()
    ingestion_service.update_document(document_id, newDocument)
    return {"message": f"Document {document_id} loader updated successfully"}   

#NOTE: This one should be written before the get_document_content endpoint because fastapi will match the first endpoint that matches the path
@ingestion.get("/loaders")
async def get_loaders():
    """Get the list of loaders supported by the document ingestion service"""
    loaders = [ loader.__name__ for loader in SUPPORTED_EXTENSIONS.values()]
    print(loaders)
    return {"loaders": loaders}

@ingestion.get("/document/{document_id}")
async def get_document_content(document_id: str):
    """Get the content of a specific document"""
    try:
        store = VectorStoreService()
        document = store.get_document(document_id)
        
        if not document:
            return JSONResponse(
                status_code=404,
                content={"message": "Document not found"}
            )
            
        
        # For other file types, return the text content
        return document
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error retrieving document: {str(e)}"}
        )

@ingestion.get("/parsers") #TODO: Remove this endpoint and use the one in parsing_routes.py
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    parser_service = ParserService()
    parsers = parser_service.get_parsers()
    return {"parsers": parsers}

@ingestion.post("/ingestion/reindex")
async def reindex_document(document_id: str, parser: str):
    """Reindex a document with new parser/loader settings"""
    try:
        vector_store = VectorStoreService()
        document = vector_store.get_document(document_id)
        # Get the document
        if not document:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Document with ID {document_id} not found",
                    "code": "DOCUMENT_NOT_FOUND"
                }
            )

        parser_service = ParserService()
        parsed_document = parser_service.parse_document(document, parser)
        
        if vector_store.update_document(document_id, parsed_document):
            return parsed_document
        else:
            return JSONResponse(
                status_code=500,
                content={"message": "Failed to reindex document"}
            )
        
    except Exception as e:
        logger.error(f"Error during reindexing process: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Failed to reindex document",
                "code": "REINDEX_FAILED",
                "error": str(e)
            }
        )
            
@ingestion.get("/upload-directory")
async def get_upload_directory():
    """Get the upload directory path"""
    return {
        "path": str(settings.paths.upload_dir)
    }
