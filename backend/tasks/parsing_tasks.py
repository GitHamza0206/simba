from celery import Celery
from core.config import settings
from models.simbadoc import SimbaDoc
from services.parser_service import ParserService
from core.factories.database_factory import get_database
import logging
import os

logger = logging.getLogger(__name__)

# Force CPU usage through environment variable
os.environ["PYTORCH_DEVICE"] = "cpu"

if settings.features.enable_parsers:
    celery = Celery('tasks')
    
    # Configure from settings
    celery.conf.update(
        broker_url=settings.celery.broker_url,
        result_backend=settings.celery.result_backend,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        enable_utc=True,
        worker_send_task_events=True,
        task_send_sent_event=True,
        worker_redirect_stdouts=False,
        worker_cancel_long_running_tasks_on_connection_loss=True,
        worker_max_tasks_per_child=100,  # Recycle workers after 100 tasks
        broker_connection_max_retries=0,  # Faster failure detection
        # Use solo pool instead of prefork to avoid MPS issues
        worker_pool='solo'
    )
else:
    celery = None  # Disable Celery when parsers are off

# Initialize parser service with explicit CPU device
parser_service = ParserService(device='cpu', force_cpu=True)

@celery.task(name="parse_markitdown", bind=True)
def parse_markitdown_task(self, document_id: str):
    db = None
    try:
        # Get fresh database connection
        db = get_database()
        logger.info(f"[Task {self.request.id}] Fetching document with ID: {document_id}")
        
        doc = db.get_document(document_id)
        if not doc:
            logger.error(f"[Task {self.request.id}] Document {document_id} not found")
            return {"status": "error", "error": "Document not found"}
            
        # Get parsed document from service
        parsed_doc = parser_service._parse_markitdown(doc)
        # Update with SimbaDoc instance
        db.update_document(document_id, parsed_doc)
        logger.info(f"[Task {self.request.id}] Successfully updated document {document_id}")
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] Parse failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        if hasattr(db, 'close'):
            db.close()

@celery.task(name="parse_docling")
def parse_docling_task(document_id: str):
    try:
        db = get_database()
        original_doc = db.get_document(document_id)
        parsed_simba_doc = parser_service.parse_document(original_doc, "docling")
        
        # Archive original document
        db.update_document(document_id, parsed_simba_doc)
        
            
        return {"status": "success", "document_id": parsed_simba_doc.id}
    except Exception as e:
        #logger.error(f"[Task {self.request.id}] Parse failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        if hasattr(db, 'close'):
            db.close() 