from celery import Celery
from core.config import settings
from models.simbadoc import SimbaDoc
from services.parser_service import ParserService
from core.factories.database_factory import get_database
import logging

logger = logging.getLogger(__name__)

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
        broker_connection_max_retries=0  # Faster failure detection
    )
else:
    celery = None  # Disable Celery when parsers are off

parser_service = ParserService()

@celery.task(name="parse_markitdown")
def parse_markitdown_task(document_id: str):
    try:
        # Get fresh database connection
        db = get_database()
        logger.info(f"Fetching document with ID: {document_id}")
        
        doc = db.get_document(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "error": "Document not found"}
            
        # Get parsed document from service
        parsed_doc = parser_service._parse_markitdown(doc)
        # Update with SimbaDoc instance
        db.update_document(document_id, parsed_doc)
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Parse failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

@celery.task(name="parse_docling")
def parse_docling_task(document_id: str):
    try:
        # Get fresh database connection
        db = get_database()
        logger.info(f"Starting docling parse for {document_id}")
        logger.info(f"Fetching document with ID: {document_id}")
        
        doc = db.get_document(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found in database")
            return {"status": "error", "error": "Document not found"}
            
        logger.info(f"Processing document: {doc.id} ({doc.metadata.file_path})")
        
        parsed_doc = parser_service._parse_docling(doc)
        db.update_document(document_id, parsed_doc)
        logger.info(f"Successfully updated document {doc.id}")
        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"Parse failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)} 