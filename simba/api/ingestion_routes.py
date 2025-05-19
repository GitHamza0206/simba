import asyncio
import io
import logging
import os
import uuid
from pathlib import Path
from typing import List, Dict, Any

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, Body
from fastapi.responses import FileResponse

from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.ingestion import Loader
from simba.ingestion.document_ingestion import DocumentIngestionService
from simba.ingestion.file_handling import save_file_locally
from simba.models.simbadoc import SimbaDoc
from simba.api.middleware.auth import get_current_user
from pydantic import BaseModel

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
    current_user: Dict[str, Any] = Depends(get_current_user)
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


class BulkIngestionRequest(BaseModel):
    folder_paths: List[str]


@ingestion.post("/ingestion/bulk")
async def ingest_bulk_folders(
    request: BulkIngestionRequest,
    destination_path: str = Query(default="/", description="Destination folder path to store the documents"),
    recursive: bool = Query(default=True, description="Whether to process subfolders recursively"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Ingest all documents from one or many folders into the vector store
    
    Args:
        folder_paths: List of folder paths to process
        destination_path: Destination folder path to store the documents
        recursive: Whether to process subfolders recursively
        current_user: Current authenticated user
        
    Returns:
        Summary of the ingestion operation
    """
    try:
        folder_paths = request.folder_paths
        # Keep track of all processed documents
        all_processed_docs = []
        # Keep track of files that failed to process
        failed_files = []
        # Keep track of skipped files (unsupported extensions)
        skipped_files = []
        
        # Get list of supported file extensions
        supported_extensions = loader.SUPPORTED_EXTENSIONS.keys()
        
        # Process each folder path
        for folder_path in folder_paths:
            path = Path(folder_path)
            
            # Check if the folder exists
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")
            
            if not path.is_dir():
                raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
                
            # Find all files in the folder (and subfolders with supported extensions)
            files_to_process = []
            
            # Function to walk directory tree
            if recursive:
                # Process directories recursively
                for root, _, files in os.walk(path):
                    root_path = Path(root)
                    for file in files:
                        file_path = root_path / file
                        extension = f".{file_path.suffix.lower().lstrip('.')}"
                        if extension in supported_extensions:
                            files_to_process.append(file_path)
                        else:
                            skipped_files.append(str(file_path))
            else:
                # Only process files in the top-level directory
                for file in path.iterdir():
                    if file.is_file():
                        extension = f".{file.suffix.lower().lstrip('.')}"
                        if extension in supported_extensions:
                            files_to_process.append(file)
                        else:
                            skipped_files.append(str(file))
                        
            logger.info(f"Found {len(files_to_process)} supported files in {folder_path}")
            
            # Process each file in the folder
            async def process_file_path(file_path):
                try:
                    # Open the file as an UploadFile
                    async with aiofiles.open(file_path, "rb") as f:
                        content = await f.read()
                        
                    # Skip empty files
                    if len(content) == 0:
                        logger.warning(f"Skipping empty file: {file_path}")
                        skipped_files.append(str(file_path))
                        return None
                        
                    file = UploadFile(
                        filename=file_path.name,
                        file=io.BytesIO(content)
                    )
                    
                    # Process the file
                    simba_doc = await ingestion_service.ingest_document(file, destination_path)
                    logger.info(f"Successfully processed file: {file_path}")
                    return simba_doc
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    failed_files.append({"path": str(file_path), "error": str(e)})
                    return None
            
            # Process files in chunks to avoid overwhelming the system
            chunk_size = 10  # Process 10 files at a time
            for i in range(0, len(files_to_process), chunk_size):
                chunk = files_to_process[i:i + chunk_size]
                results = await asyncio.gather(*[process_file_path(file_path) for file_path in chunk])
                # Filter out None results (failed processing)
                valid_results = [doc for doc in results if doc is not None]
                all_processed_docs.extend(valid_results)
                
                # Insert documents in batches
                if valid_results:
                    db.insert_documents(valid_results, user_id=current_user["id"])
                    
                # Log progress
                logger.info(f"Processed {i + len(chunk)} of {len(files_to_process)} files from {folder_path}")
        
        # Return summary of the operation
        return {
            "message": f"Bulk ingestion completed from {len(folder_paths)} folders",
            "processed_count": len(all_processed_docs),
            "failed_count": len(failed_files),
            "skipped_count": len(skipped_files),
            "failed_files": failed_files,
            "processed_docs": [doc.id for doc in all_processed_docs]
        }
        
    except Exception as e:
        logger.error(f"Error in ingest_bulk_folders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ingestion.put("/ingestion/update_document")
async def update_document(
    doc_id: str, 
    new_simbadoc: SimbaDoc, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a document"""
    try:
        # Update the document in the database for the current user only
        success = db.update_document(doc_id, new_simbadoc, user_id=current_user["id"])
        if not success:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found or you don't have access to it")

        return new_simbadoc
    except Exception as e:
        logger.error(f"Error in update_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ingestion.get("/ingestion")
async def get_ingestion_documents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all ingested documents for the current user"""
    # Get documents for the current user only
    documents = db.get_all_documents(user_id=current_user["id"])
    return documents


@ingestion.get("/ingestion/{uid}")
async def get_document(
    uid: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a document by ID"""
    # Get document for the current user only
    document = db.get_document(uid, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail=f"Document {uid} not found or you don't have access to it")
    return document


@ingestion.delete("/ingestion")
async def delete_document(
    uids: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a document by ID"""
    try:
        # Delete documents from vector store
        for uid in uids:
            # Get document for the current user only
            simbadoc = db.get_document(uid, user_id=current_user["id"])
            if not simbadoc:
                raise HTTPException(status_code=404, detail=f"Document {uid} not found or you don't have access to it")
                
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
async def preview_document(
    doc_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a file for preview by document ID"""
    try:
        # Retrieve document from database for the current user only
        document = db.get_document(doc_id, user_id=current_user["id"])
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found or you don't have access to it")

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
