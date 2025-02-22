import os
import logging
from pathlib import Path
from celery import Celery
from celery.signals import worker_init, worker_shutdown, worker_shutting_down
import torch


from simba.core.config import settings

logger = logging.getLogger(__name__)

def get_celery_config():
    """
    Returns the Celery configuration dictionary with all settings
    """
    return {
        'broker_url': settings.celery.broker_url,
        'result_backend': settings.celery.result_backend,
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'enable_utc': True,
        'worker_send_task_events': True,
        'task_send_sent_event': True,
        'worker_redirect_stdouts': False,
        'worker_cancel_long_running_tasks_on_connection_loss': True,
        'worker_max_tasks_per_child': 1,  # Recycle workers after each task
        'broker_connection_max_retries': 0,  # Faster failure detection
        'worker_pool': 'solo',  # Use solo pool to avoid multiprocessing issues
        'worker_max_memory_per_child': 1000000,  # 1GB memory limit per worker
        'task_time_limit': 3600,  # 1 hour time limit per task
        'task_soft_time_limit': 3000,  # 50 minutes soft time limit,
        'worker_shutdown_timeout': 10,  # Give tasks 10 seconds to clean up
        'imports': ['simba.tasks.parsing_tasks'],
        'task_routes': {
            'parse_markitdown': {'queue': 'parsing'},
            'parse_docling': {'queue': 'parsing'}
        }
    }

def create_celery_app():
    """
    Creates and configures the Celery application with proper shutdown handling
    """
    app = Celery('simba')
    app.conf.update(get_celery_config())
    
    @worker_init.connect
    def init_worker(sender=None, **kwargs):
        logger.info(f"🚀 Starting Celery worker with broker: {settings.celery.broker_url}")
    
    @worker_shutting_down.connect
    def handle_shutdown(sender=None, **kwargs):
        logger.info("🛑 Worker shutting down, clearing CUDA cache")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    @worker_shutdown.connect
    def worker_shutdown_handler(**kwargs):
        logger.info("Celery worker shutdown complete")
    
    return app

# Create the celery application
celery_app = create_celery_app()