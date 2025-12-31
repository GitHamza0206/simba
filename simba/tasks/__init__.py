"""Celery background tasks."""

from simba.tasks.ingestion_tasks import process_document

__all__ = ["process_document"]
