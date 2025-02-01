from celery import Celery
from core.config import settings
from core.factories.vector_store_factory import VectorStoreFactory
from models.simbadoc import SimbaDoc
from services.parser_service import ParserService
from core.factories.database_factory import get_database
import logging
import os
import torch

logger = logging.getLogger(__name__)

# Force CPU usage through environment variables
os.environ["PYTORCH_DEVICE"] = "cpu"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable CUDA
os.environ["TORCH_DEVICE"] = "cpu"  # Force PyTorch to use CPU

# Ensure PyTorch is using CPU
if torch.cuda.is_available():
    torch.cuda.empty_cache()
torch.set_num_threads(1)  # Limit to single thread to avoid conflicts

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
        worker_max_tasks_per_child=1,  # Recycle workers after each task
        broker_connection_max_retries=0,  # Faster failure detection
        worker_pool='solo',  # Use solo pool to avoid multiprocessing issues
        worker_max_memory_per_child=1000000,  # 1GB memory limit per worker
        task_time_limit=3600,  # 1 hour time limit per task
        task_soft_time_limit=3000,  # 50 minutes soft time limit
    )
else:
    celery = None  # Disable Celery when parsers are off

# Initialize parser service with explicit CPU device and force CPU flag
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
        # Ensure we're using CPU for this task
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        db = get_database()
        original_doc = db.get_document(document_id)
        
        # Explicitly run parsing on CPU
        with torch.no_grad():  # Disable gradient computation
            parsed_simba_doc = parser_service.parse_document(original_doc, "docling")
        
        # Update database
        db.update_document(document_id, parsed_simba_doc)

        # Sync vector store
        vector_store = VectorStoreFactory.get_vector_store()
        # Delete old chunks
        if original_doc and original_doc.documents:
            vector_store.delete_documents([doc.id for doc in original_doc.documents])   
        # Add new chunks
        if parsed_simba_doc and parsed_simba_doc.documents:
            vector_store.add_documents(parsed_simba_doc.documents)
            
        return {"status": "success", "document_id": parsed_simba_doc.id}
    except Exception as e:
        logger.error(f"Parse failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        if hasattr(db, 'close'):
            db.close()
        # Clean up any remaining GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()