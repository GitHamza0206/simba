import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import aiofiles
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.ingestion import Loader
from simba.ingestion.document_ingestion import DocumentIngestionService
from simba.ingestion.file_handling import delete_file_locally, save_file_locally
from simba.models.simbadoc import SimbaDoc
from simba.tasks.ingestion_tasks import ingest_document_task

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

ingestion = APIRouter()

ingestion_service = DocumentIngestionService()
db = get_database()
loader = Loader()
kms = DocumentIngestionService()
store = VectorStoreFactory.get_vector_store()


def submit_ingestion_task(file_info: Dict[str, Any], folder_path: str):
    """Submit a single ingestion task to Celery and log the result"""
    try:
        # Extract and validate the file path
        if not isinstance(file_info, dict):
            logger.error(f"Invalid file_info type: {type(file_info)}")
            return {
                "task_id": "error",
                "filename": "unknown",
                "status": "error",
                "message": "Invalid file information format",
            }

        file_path = file_info.get("path")
        filename = file_info.get("filename", "unknown")

        # Handle None or empty path
        if file_path is None or file_path == "None" or file_path == "":
            error_msg = f"Invalid file path '{file_path}' for file {filename}"
            logger.error(error_msg)
            return {
                "task_id": "error",
                "filename": filename,
                "status": "error",
                "message": error_msg,
            }

        # Ensure it's a string
        file_path = str(file_path).strip()

        # Validate the path format
        try:
            path_obj = Path(file_path)
            if not path_obj.is_absolute():
                logger.warning(f"Received relative path: {file_path}. Converting to absolute.")
                file_path = str(path_obj.resolve())
        except Exception as e:
            logger.error(f"Invalid path format: {file_path}, error: {str(e)}")
            return {
                "task_id": "error",
                "filename": filename,
                "status": "error",
                "message": f"Invalid file path format: {str(e)}",
            }

        # Check if file still exists
        if not os.path.exists(file_path):
            error_msg = f"File not found before task submission: {file_path}"
            logger.error(error_msg)
            return {
                "task_id": "error",
                "filename": filename,
                "status": "error",
                "message": error_msg,
            }

        # Check file size
        try:
            file_size = file_info.get("size", 0)
            if file_size <= 0:
                file_size = os.path.getsize(file_path)
                logger.warning(f"Missing or invalid file size, calculated as: {file_size}")
        except Exception as e:
            logger.error(f"Error checking file size: {str(e)}")
            file_size = 0

        # Submit task
        logger.info(
            f"Submitting ingestion task for file: {filename} at path: {file_path}, size: {file_size}"
        )
        try:
            # Try to submit the task to Celery
            task = ingest_document_task.delay(
                file_path=file_path,
                file_name=filename,
                file_size=file_size,
                folder_path=folder_path,
            )

            # Verify Celery accepted the task by checking if we can access the task ID
            # This will fail if Celery is not responding
            if not task or not task.id:
                raise Exception("Celery did not return a valid task ID")

            logger.info(f"Task submitted with ID: {task.id}")
            return {
                "task_id": task.id,
                "filename": filename,
                "status": "processing",
                "message": f"Document {filename} queued for ingestion",
            }

        except Exception as celery_error:
            # Celery failed or didn't respond, fall back to synchronous processing
            logger.warning(
                f"Celery task submission failed: {str(celery_error)}. Falling back to synchronous processing."
            )

            try:
                # Create a synchronous context for the async ingestion
                loop = asyncio.get_event_loop()

                # Simulate the functionality of the Celery task
                class MockUploadFile:
                    def __init__(self, filename, size):
                        self.filename = filename
                        self.size = size
                        self._file_path = file_path

                    async def read(self):
                        async with aiofiles.open(self._file_path, "rb") as f:
                            return await f.read()

                    async def seek(self, position):
                        pass  # No need to implement for synchronous processing

                    async def close(self):
                        pass  # No need to implement for synchronous processing

                # Create a mock UploadFile object
                mock_file = MockUploadFile(filename=filename, size=file_size)

                # Create a document ingestion service
                ingestion_service = DocumentIngestionService()

                # Run the ingest_document method synchronously
                doc = loop.run_until_complete(
                    ingestion_service.ingest_document(file=mock_file, file_path=file_path)
                )

                logger.info(f"Synchronous processing complete for {filename}")
                return {
                    "task_id": f"sync-{uuid.uuid4()}",  # Generate a unique ID for the sync task
                    "filename": filename,
                    "status": "completed",  # Mark as completed since it's done synchronously
                    "message": f"Document {filename} processed synchronously",
                    "doc_id": doc.metadata.get("id") if doc and hasattr(doc, "metadata") else None,
                }

            except Exception as sync_error:
                logger.error(
                    f"Synchronous processing also failed: {str(sync_error)}", exc_info=True
                )
                return {
                    "task_id": "error",
                    "filename": filename,
                    "status": "error",
                    "message": f"Failed to process document (both async and sync): {str(sync_error)}",
                }
    except Exception as e:
        logger.error(f"Error submitting task for {filename}: {str(e)}", exc_info=True)
        return {
            "task_id": "error",
            "filename": filename,
            "status": "error",
            "message": f"Failed to queue document: {str(e)}",
        }


# Document Management Routes
# ------------------------


@ingestion.post("/ingestion")
async def ingest_document(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    folder_path: str = Query(default="/", description="Folder path to store the document"),
):
    """Ingest a document into the vector store"""
    try:
        store_path = Path(settings.paths.upload_dir)
        if folder_path != "/":
            store_path = store_path / folder_path.strip("/")

        logger.info(f"Received request to ingest {len(files)} files to folder {folder_path}")

        # Ensure the directory exists
        os.makedirs(store_path, exist_ok=True)

        # Process files by saving them locally first and then triggering Celery tasks
        task_results = []
        saved_files = []

        # Log the start of file saving
        logger.info(f"Starting to save {len(files)} files locally")

        # Save all files first before creating tasks to avoid resource contention
        for file in files:
            try:
                await file.seek(0)
                file_path = await save_file_locally(file, store_path)

                # Ensure we have a valid file path
                if file_path is None:
                    raise ValueError(
                        f"Failed to save file {file.filename}: save_file_locally returned None"
                    )

                # Convert Path to string for logging and serialization
                file_path_str = str(file_path)

                # Get file size without loading entire file into memory
                file_stat = Path(file_path).stat()
                file_size = file_stat.st_size

                logger.info(
                    f"Saved file {file.filename} to {file_path_str} (size: {file_size} bytes)"
                )

                saved_files.append(
                    {
                        "filename": file.filename,
                        "path": file_path_str,  # Use string representation
                        "size": file_size,
                    }
                )

            except Exception as e:
                logger.error(f"Error saving file {file.filename}: {str(e)}", exc_info=True)
                # Continue with other files even if one fails
                task_results.append(
                    {
                        "task_id": "error",
                        "filename": file.filename,
                        "status": "error",
                        "message": f"Failed to save file: {str(e)}",
                    }
                )
                continue

        # Start a few tasks immediately to avoid UX lag
        initial_batch_size = min(2, len(saved_files))

        # Process the first few files immediately for better UX
        for i in range(initial_batch_size):
            if i < len(saved_files):
                task_result = submit_ingestion_task(saved_files[i], folder_path)
                if task_result:
                    task_results.append(task_result)

        # Schedule the rest to be processed in the background
        if len(saved_files) > initial_batch_size:
            # Add the background task
            background_tasks.add_task(
                process_remaining_files, saved_files[initial_batch_size:], folder_path
            )

            # Add placeholder results for the files that will be processed in the background
            for file_info in saved_files[initial_batch_size:]:
                task_results.append(
                    {
                        "task_id": "queued",
                        "filename": file_info["filename"],
                        "status": "queued",
                        "message": f"Document {file_info['filename']} will be processed shortly",
                    }
                )

        logger.info(f"Returning response with {len(task_results)} task results")
        return {"tasks": task_results}

    except Exception as e:
        logger.error(f"Error in ingest_document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def process_remaining_files(saved_files: List[Dict[str, Any]], folder_path: str):
    """Process remaining files in the background to avoid blocking the API response"""
    try:
        logger.info(f"Starting background processing of {len(saved_files)} files")
        task_results = []

        for file_info in saved_files:
            # Add a small delay to reduce contention
            await asyncio.sleep(1)

            try:
                # Skip files without a valid path
                if not file_info or not isinstance(file_info, dict):
                    logger.error("Invalid file_info object in process_remaining_files")
                    continue

                file_path = file_info.get("path")
                filename = file_info.get("filename", "unknown")

                if not file_path:
                    logger.error(f"Missing file path for file {filename}")
                    continue

                # Check if file still exists before processing
                if not os.path.exists(str(file_path)):
                    logger.error(f"File no longer exists at {file_path}, skipping")
                    continue

                # Submit the task with proper error handling
                try:
                    task_result = submit_ingestion_task(file_info, folder_path)
                    if task_result:
                        task_results.append(task_result)
                    logger.info(f"Background task submitted for {filename}")
                except Exception as e:
                    logger.error(f"Error submitting background task for {filename}: {str(e)}")

            except Exception as e:
                logger.error(f"Error processing file in background: {str(e)}")
                # Continue with other files even if one fails
                continue

        logger.info(f"Background processing completed for {len(task_results)} files")
        return task_results

    except Exception as e:
        logger.error(f"Error in background processing: {str(e)}", exc_info=True)


@ingestion.get("/ingestion/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a document ingestion task"""
    try:
        # Get the task result
        task = ingest_document_task.AsyncResult(task_id)

        if task.state == "PENDING":
            response = {"status": "pending", "message": "Task is pending"}
        elif task.state == "FAILURE":
            response = {"status": "failure", "message": str(task.info)}
        else:
            response = {"status": task.state.lower(), "message": task.info}

        return response

    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
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


@ingestion.get("/parsers")
async def get_parsers():
    """Get supported parsers"""
    return {"parsers": "docling"}


@ingestion.get("/upload-directory")
async def get_upload_directory():
    """Get upload directory path"""
    return {"path": str(settings.paths.upload_dir)}


@ingestion.get("/preview/{doc_id}")
async def preview_document(doc_id: str):
    """Get a file for preview by document ID"""
    try:
        # Retrieve document from database
        document = db.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

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

        # Custom headers for better browser handling
        headers = {
            "Content-Disposition": f'inline; filename="{document.metadata.filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Access-Control-Allow-Origin": "*",  # Allow CORS for iframe access
        }

        # Log file details for debugging
        logger.info(
            f"Serving file: {absolute_path}, size: {absolute_path.stat().st_size}, media_type: {media_type}"
        )

        # Return file response with headers
        return FileResponse(
            path=str(absolute_path),
            media_type=media_type,
            filename=document.metadata.filename,
            headers=headers,
        )
    except Exception as e:
        logger.error(f"Error in preview_document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
