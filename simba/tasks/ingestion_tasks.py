import asyncio
import gc
import logging
import os
from pathlib import Path

import aiofiles
import torch
from celery import shared_task

from simba.core.celery_config import celery_app as celery
from simba.core.factories.database_factory import get_database
from simba.ingestion.document_ingestion import DocumentIngestionService

logger = logging.getLogger(__name__)


@celery.task(
    name="ingest_document",
    bind=True,
    max_retries=3,
    serializer="json",
    acks_late=True,  # Only acknowledge the task after it's been processed
    reject_on_worker_lost=True,  # Requeue the task if the worker is lost
)
def ingest_document_task(
    self, file_path: str, file_name: str, file_size: int, folder_path: str = "/"
):
    """
    Celery task to process and ingest documents into the vector store asynchronously.

    Args:
        file_path: Path to the uploaded file
        file_name: Original filename
        file_size: Size of the file in bytes
        folder_path: Optional folder path for organizing documents

    Returns:
        Dict containing the status and document ID
    """
    db = None
    loop = None

    # Log the task execution for debugging
    logger.info(
        f"Starting ingestion task for file: {file_name} (size: {file_size}, path: {file_path})"
    )

    # Enhanced error handling for None paths
    if file_path is None or file_path == "None":
        error_msg = "File path is None or string 'None', cannot process"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}

    # Ensure file_path is a string and properly formatted
    try:
        file_path = str(file_path).strip()
        if not file_path:
            raise ValueError("Empty file path")
    except Exception as e:
        error_msg = f"Invalid file path format: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}

    # Verify file exists with more detailed error
    if not os.path.exists(file_path):
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        # Check if directory exists
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            logger.error(f"Directory also does not exist: {dir_path}")
        return {"status": "error", "error": error_msg}

    try:
        # Force garbage collection before starting
        gc.collect()

        # Use database as a local variable to ensure proper cleanup
        db = get_database()
        ingestion_service = DocumentIngestionService()

        # Create a more complete mock UploadFile object with the necessary attributes
        class MockUploadFile:
            def __init__(self, filename, size):
                self.filename = filename
                self.size = size
                self._file_path = file_path  # Store file path for reference
                self._file_position = 0  # Track file position

            async def read(self):
                """Implement robust file reading with error handling"""
                try:
                    if not os.path.exists(self._file_path):
                        logger.error(f"File not found during read: {self._file_path}")
                        raise FileNotFoundError(f"File not found: {self._file_path}")

                    async with aiofiles.open(self._file_path, "rb") as f:
                        await f.seek(self._file_position)
                        content = await f.read()
                        self._file_position = self._file_position + len(content)  # Update position
                        return content
                except Exception as e:
                    logger.error(f"Error reading file {self.filename}: {str(e)}")
                    raise

            async def seek(self, position):
                """Implement proper seek with position tracking"""
                if position < 0:
                    raise ValueError(f"Invalid seek position: {position}")
                self._file_position = position
                return None

            async def close(self):
                """Mock close method for compatibility"""
                self._file_position = 0
                return None

        mock_file = MockUploadFile(filename=file_name, size=file_size)

        # Use synchronous processing since we're in a Celery task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Log progress
        logger.info(f"Processing document: {file_name}")

        # Process the document
        simba_doc = loop.run_until_complete(ingestion_service.ingest_document(mock_file, file_path))

        # Insert into database
        logger.info(f"Inserting document into database: {simba_doc.id}")
        db.insert_documents([simba_doc])

        logger.info(f"Document processed successfully: {file_name} (ID: {simba_doc.id})")

        return {
            "status": "success",
            "document_id": simba_doc.id,
            "message": f"Document {file_name} ingested successfully",
        }

    except Exception as e:
        logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)

        # Retry the task with exponential backoff if it's a transient error
        # This helps with resource contention issues
        try:
            if self.request.retries < self.max_retries:
                # Exponential backoff: 2^retries seconds (2, 4, 8, etc.)
                retry_delay = 2**self.request.retries
                logger.info(
                    f"Retrying task in {retry_delay} seconds (attempt {self.request.retries + 1})"
                )
                raise self.retry(countdown=retry_delay, exc=e)
        except Exception as retry_error:
            logger.error(f"Retry failed: {str(retry_error)}")

        return {"status": "error", "error": str(e)}
    finally:
        # Explicitly clean up resources
        if db and hasattr(db, "close"):
            try:
                db.close()
            except Exception as e:
                logger.error(f"Error closing database: {str(e)}")

        # Clean up the event loop
        if loop:
            try:
                loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {str(e)}")

        # Clean up GPU memory if available
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception as e:
                logger.error(f"Error cleaning GPU cache: {str(e)}")

        # Force garbage collection again
        gc.collect()
