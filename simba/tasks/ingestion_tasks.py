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


class MockUploadFile:
    """A mock UploadFile for Celery ingestion tasks."""
    def __init__(self, filename: str, size: int, file_path: str):
        self.filename = filename
        self.size = size
        self._file_path = file_path
        self._file_position = 0

    async def read(self):
        if not os.path.exists(self._file_path):
            raise FileNotFoundError(f"File not found: {self._file_path}")
        async with aiofiles.open(self._file_path, "rb") as f:
            await f.seek(self._file_position)
            content = await f.read()
            self._file_position += len(content)
            return content

    async def seek(self, position: int):
        if position < 0:
            raise ValueError(f"Invalid seek position: {position}")
        self._file_position = position

    async def close(self):
        self._file_position = 0


def _validate_file_path(file_path: str) -> str:
    """Validate and clean the file path."""
    if not file_path or file_path in (None, "None"):
        raise ValueError("File path is None or empty.")
    file_path = str(file_path).strip()
    if not file_path:
        raise ValueError("File path is empty after stripping.")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path


def _cleanup_resources(db, loop):
    if db and hasattr(db, "close"):
        try:
            db.close()
        except Exception:
            pass
    if loop:
        try:
            loop.close()
        except Exception:
            pass
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass
    gc.collect()


@celery.task(
    name="ingest_document",
    bind=True,
    max_retries=3,
    serializer="json",
    acks_late=True,
    reject_on_worker_lost=True,
)
def ingest_document_task(self, file_path: str, file_name: str, file_size: int, folder_path: str = "/"):
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
    try:
        logger.info(f"[Ingestion] Starting for file: {file_name} (size: {file_size}, path: {file_path})")
        file_path = _validate_file_path(file_path)
        db = get_database()
        ingestion_service = DocumentIngestionService()
        mock_file = MockUploadFile(filename=file_name, size=file_size, file_path=file_path)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        simba_doc = loop.run_until_complete(ingestion_service.ingest_document(mock_file, folder_path))
        db.insert_documents([simba_doc])
        logger.info(f"[Ingestion] Success: {file_name} (ID: {simba_doc.id})")
        return {
            "status": "success",
            "document_id": simba_doc.id,
            "message": f"Document {file_name} ingested successfully",
        }
    except Exception as e:
        logger.error(f"[Ingestion] Failed: {str(e)}", exc_info=True)
        if self.request.retries < self.max_retries:
            retry_delay = 2 ** self.request.retries
            logger.info(f"Retrying in {retry_delay} seconds (attempt {self.request.retries + 1})")
            try:
                raise self.retry(countdown=retry_delay, exc=e)
            except Exception:
                pass
        return {"status": "error", "error": str(e)}
    finally:
        _cleanup_resources(db, loop)
