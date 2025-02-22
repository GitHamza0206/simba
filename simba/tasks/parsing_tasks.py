import logging
import os

import torch
from simba.core.celery_config import celery_app as celery  # Rename for backward compatibility
from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.models.simbadoc import SimbaDoc
from simba.parsing.docling_parser import DoclingParser

logger = logging.getLogger(__name__)

vector_store = VectorStoreFactory.get_vector_store()

@celery.task(name="parse_docling")
def parse_docling_task(document_id: str):
    try:        
        parser = DoclingParser() 
        db = get_database()
        
        original_doc = db.get_document(document_id)
        

        parsed_simba_doc = parser.parse(original_doc)
        
        # Update database

        vector_store.add_documents(parsed_simba_doc.documents)
        print("---")
        print("adding documents to store : ", parsed_simba_doc.documents)
        print("---")

        db.update_document(document_id, parsed_simba_doc)

            
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