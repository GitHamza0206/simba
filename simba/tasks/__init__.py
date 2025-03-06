"""
Task modules for the Simba application.

This package contains Celery task definitions for asynchronous processing.
"""

# Import the task functions to make them available from the tasks package
from simba.tasks.parsing_tasks import parse_docling_task
from simba.tasks.ingestion_tasks import ingest_document_task

__all__ = ["parse_docling_task", "ingest_document_task"]
