"""Background tasks for document ingestion."""

import logging

from simba.core.celery_config import celery_app
from simba.models import SessionLocal
from simba.services import ingestion_service

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="simba.tasks.ingestion_tasks.process_document",
    max_retries=3,
    default_retry_delay=60,
)
def process_document(self, document_id: str) -> dict:
    """Background task to process a document through the ingestion pipeline.

    Args:
        document_id: ID of the document to process.

    Returns:
        Dict with task result status.
    """
    logger.info(f"Starting document processing task for: {document_id}")

    db = SessionLocal()
    try:
        ingestion_service.ingest_document(document_id, db)
        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"Document processing failed: {e}")

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "failed", "document_id": document_id, "error": str(e)}

    finally:
        db.close()
