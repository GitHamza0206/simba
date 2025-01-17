from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import base64
import os
from pathlib import Path

from typing import List
from services.ingestion_service.config import SUPPORTED_EXTENSIONS
from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from services.ingestion_service.file_handling import load_file_from_path
from services.ingestion_service.types import IngestedDocument
from services.parser_service import ParserService
from services.vector_store_service import VectorStoreService
from core.config import settings

from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

ingestion = APIRouter()

@ingestion.delete("/ingestion")
async def delete_ingestion_documents(uid: str)->dict :
    ingestion_service = DocumentIngestionService()
    ingestion_service.delete_ingested_document(uid)
    return {"message": f"Document {uid} deleted successfully"}

@ingestion.get("/ingestion")
async def get_ingestion_documents():
    ingestion_service = DocumentIngestionService()
    ingested_documents = ingestion_service.get_ingested_documents()
    return ingested_documents

@ingestion.post("/ingestion")
async def ingest_document(file: UploadFile = File(...)):
    """Ingest documents into the vector store"""

    try:
        ingestion_service = DocumentIngestionService()
        result = ingestion_service.ingest_document(file)
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




@ingestion.post("/ingestion/{document_id}/reindex")
async def reindex_document(document_id: str):
    """Reindex a document with new parser/loader settings"""
    try:
        ingestion_service = DocumentIngestionService()

        # Get the document
        document = ingestion_service.get_document(document_id)
        if not document:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Document with ID {document_id} not found",
                    "code": "DOCUMENT_NOT_FOUND"
                }
            )

        # Get file path from metadata
        file_path = document.metadata.get('file_path')
        file_path = file_path.split('.')[0] + '.md'

        if not file_path:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Document metadata is missing file path",
                    "code": "INVALID_METADATA"
                }
            )

        # Convert to Path object and make it absolute
        if isinstance(file_path, str):
            file_path = settings.paths.base_dir / file_path

        # Verify the file exists
        try:
            if file_path.exists():
                file = UploadFile(
                    file=open(file_path, 'rb'),
                    filename=file_path.name
                )
            else:
                return JSONResponse(
                    status_code=404,
                    content={
                        "detail": f"File not found at {file_path}",
                        "code": "FILE_NOT_FOUND"
                    }
                )

            # Perform reindexing
            ingestion_service.delete_ingested_document(document_id)
            new_doc = ingestion_service.ingest_document(file)
            
            return new_doc
        
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
            
    except Exception as e:
        logger.error(f"Unexpected error during reindex operation: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
                "error": str(e)
            }
        )
