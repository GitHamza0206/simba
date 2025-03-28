import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from simba.api.middleware.auth import get_current_user
from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.ingestion import Loader
from simba.ingestion.document_ingestion import DocumentIngestionService
from simba.ingestion.file_handling import save_file_locally
from simba.models.simbadoc import SimbaDoc

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
    folder_path: str = Query(default="/", description="Folder path to store the document"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Ingest a document into the vector store"""
    try:
        # Process files concurrently using asyncio.gather
        async def process_file(file):
            simba_doc = await ingestion_service.ingest_document(file, folder_path)
            return simba_doc

        # Process all files concurrently
        response = await asyncio.gather(*[process_file(file) for file in files])
        # Insert into database with user_id
        db.insert_documents(response, user_id=current_user["id"])
        return response

    except Exception as e:
        logger.error(f"Error in ingest_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ingestion.put("/ingestion/update_document")
async def update_document(
    doc_id: str, new_simbadoc: SimbaDoc, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a document"""
    try:
        # Update the document in the database for the current user only
        success = db.update_document(doc_id, new_simbadoc, user_id=current_user["id"])
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Document {doc_id} not found or you don't have access to it",
            )

        return new_simbadoc
    except Exception as e:
        logger.error(f"Error in update_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ingestion.get("/ingestion")
async def get_ingestion_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all ingested documents for the current user"""
    # Get documents for the current user only
    documents = db.get_all_documents(user_id=current_user["id"])
    return documents


@ingestion.get("/ingestion/{uid}")
async def get_document(uid: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get a document by ID"""
    # Get document for the current user only
    document = db.get_document(uid, user_id=current_user["id"])
    if not document:
        raise HTTPException(
            status_code=404, detail=f"Document {uid} not found or you don't have access to it"
        )
    return document


@ingestion.delete("/ingestion")
async def delete_document(
    uids: List[str], current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a document by ID"""
    try:
        # Delete documents from vector store
        for uid in uids:
            # Get document for the current user only
            simbadoc = db.get_document(uid, user_id=current_user["id"])
            if not simbadoc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document {uid} not found or you don't have access to it",
                )

            if simbadoc and simbadoc.metadata.enabled:
                try:
                    store.delete_documents([doc.id for doc in simbadoc.documents])
                except Exception as e:
                    # Log the error but continue with deletion
                    logger.warning(
                        f"Error deleting document {uid} from vector store: {str(e)}. Continuing with database deletion."
                    )

        # Delete documents from database for the current user only
        for uid in uids:
            db.delete_document(uid, user_id=current_user["id"])

        # kms.sync_with_store()
        return {"message": f"Documents {uids} deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Routes
# -------------


@ingestion.get("/loaders")
async def get_loaders():
    """Get supported document loaders"""
    return {
        "loaders": [loader_name.__name__ for loader_name in loader.SUPPORTED_EXTENSIONS.values()]
    }


@ingestion.get("/upload-directory")
async def get_upload_directory():
    """Get upload directory path"""
    return {"path": str(settings.paths.upload_dir)}


@ingestion.get("/preview/{doc_id}")
async def preview_document(doc_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get a file for preview by document ID"""
    try:
        # Retrieve document from database for the current user only
        document = db.get_document(doc_id, user_id=current_user["id"])
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {doc_id} not found or you don't have access to it",
            )

        # Get file path from document metadata
        file_path = document.metadata.file_path
        if not file_path:
            raise HTTPException(status_code=404, detail="File path not found in document metadata")

        # Get upload directory
        upload_dir = Path(settings.paths.upload_dir)

        # Try multiple approaches to find the file
        possible_paths = [
            # 1. As a direct absolute path
            Path(file_path),
            # 2. As a path relative to the upload directory
            upload_dir / file_path.lstrip("/"),
            # 3. Just the filename in the upload directory
            upload_dir / Path(file_path).name,
        ]

        # Find the first path that exists
        absolute_path = None
        for path in possible_paths:
            if path.exists():
                absolute_path = path
                logger.info(f"Found file at: {path}")
                break
            else:
                logger.debug(f"File not found at: {path}")

        # If no path exists, raise 404
        if not absolute_path:
            logger.error(f"File not found. Tried paths: {possible_paths}")
            raise HTTPException(
                status_code=404, detail=f"File not found. Tried: {[str(p) for p in possible_paths]}"
            )

        # Determine media type based on file extension
        extension = absolute_path.suffix.lower()
        media_type = "application/octet-stream"  # Default

        # Set appropriate media type for common file types
        if extension == ".pdf":
            media_type = "application/pdf"
        elif extension in [".jpg", ".jpeg"]:
            media_type = "image/jpeg"
        elif extension == ".png":
            media_type = "image/png"
        elif extension == ".txt":
            media_type = "text/plain"
        elif extension == ".html":
            media_type = "text/html"
        elif extension in [".doc", ".docx"]:
            media_type = "application/msword"
        elif extension in [".xls", ".xlsx"]:
            media_type = "application/vnd.ms-excel"

        # Log file details for debugging
        logger.info(
            f"Serving file: {absolute_path}, size: {absolute_path.stat().st_size}, media_type: {media_type}"
        )

        # Get a safe filename for Content-Disposition header
        safe_filename = document.metadata.filename
        try:
            # Encode non-ASCII characters as per RFC 5987
            # See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition
            import urllib.parse

            encoded_filename = urllib.parse.quote(safe_filename)
            content_disposition = (
                f"inline; filename=\"{encoded_filename}\"; filename*=UTF-8''{encoded_filename}"
            )
        except Exception as e:
            logger.warning(f"Error encoding filename '{safe_filename}': {str(e)}")
            # Fallback to a simple ASCII filename if encoding fails
            content_disposition = 'inline; filename="document"'

        # Custom headers for better browser handling
        headers = {
            "Content-Disposition": content_disposition,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",  # Allow CORS for iframe access
        }

        # Return file response with headers
        return FileResponse(
            path=str(absolute_path),
            media_type=media_type,
            filename=None,  # Don't let FileResponse set this, we're handling it in headers
            headers=headers,
        )
    except Exception as e:
        logger.error(f"Error in preview_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
