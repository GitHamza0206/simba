"""Celery configuration and app setup."""

from celery import Celery

from simba.core.config import settings

# Create Celery app
celery_app = Celery(
    "simba",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["simba.tasks.ingestion_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Route tasks to ingestion queue
    task_routes={
        "simba.tasks.ingestion_tasks.*": {"queue": "ingestion"},
    },
)
