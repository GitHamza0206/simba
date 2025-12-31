"""Celery background tasks."""

from simba.core.celery_config import celery_app
from simba.tasks.ingestion_tasks import process_document

# Alias for Celery CLI (looks for 'app' or 'celery' by default)
app = celery_app

__all__ = ["app", "celery_app", "process_document"]
