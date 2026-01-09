"""Celery configuration and app setup."""

import ssl

from celery import Celery

from simba.core.config import settings


def _fix_redis_ssl_url(url: str) -> str:
    """Add SSL cert requirements to rediss:// URLs if not present."""
    if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}ssl_cert_reqs=CERT_NONE"
    return url


def _is_redis_ssl(url: str) -> bool:
    """Check if Redis URL uses SSL."""
    return url.startswith("rediss://")


broker_url = _fix_redis_ssl_url(settings.celery_broker_url)
backend_url = _fix_redis_ssl_url(settings.celery_result_backend)

# Create Celery app
celery_app = Celery(
    "simba",
    broker=broker_url,
    backend=backend_url,
    include=["simba.tasks.ingestion_tasks"],
)

# SSL configuration for Redis
ssl_config = {"ssl_cert_reqs": ssl.CERT_NONE} if _is_redis_ssl(broker_url) else None

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
    # SSL settings for Redis
    broker_use_ssl=ssl_config,
    redis_backend_use_ssl=ssl_config,
)
