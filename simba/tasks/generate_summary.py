import logging
from simba.core.celery_config import celery_app as celery
from simba.core.factories.database_factory import get_database
from simba.ingestion.summary import summarize_document
from simba.models.simbadoc import SimbaDoc
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

@celery.task(name="generate_summary_task")
def generate_summary_task(simbadoc_dict: dict):
    """
    Generate a summary for a document and update its metadata.
    
    Args:
        simbadoc_dict: SimbaDoc as a dictionary to summarize
        
    Returns:
        Dictionary with status information
    """
    try:
        # Reconstruct SimbaDoc from dict
        simbadoc = SimbaDoc.model_validate(simbadoc_dict)
        logger.info(f"[SUMMARY] Processing document: id={simbadoc.id}, filename={getattr(simbadoc.metadata, 'filename', None)}, metadata={simbadoc.metadata}")
        # Check if summary already exists
        if hasattr(simbadoc.metadata, "summary") and simbadoc.metadata.summary:
            logger.info(f"[SUMMARY] Document {simbadoc.id} already has a summary: {simbadoc.metadata.summary}")
            return {"status": "skipped", "reason": "Already summarized"}
        
        # Generate summary
        summary = summarize_document(simbadoc)
        logger.info(f"[SUMMARY] Generated summary for document {simbadoc.id}: {summary}")
        
        # Attach summary to metadata (as attribute and dict for compatibility)
        setattr(simbadoc.metadata, "summary", summary)
        if hasattr(simbadoc.metadata, "__dict__"):
            simbadoc.metadata.__dict__["summary"] = summary
        
        # Update in database - only get db connection when needed
        db = get_database()
        db.update_document(simbadoc.id, simbadoc)
        logger.info(f"[SUMMARY] Summary saved for document {simbadoc.id}.")
        
        return {"status": "success", "document_id": simbadoc.id}
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}


@celery.task(name="catchup_summaries_task")
def catchup_summaries_task(batch_size: int = 20):
    """
    Periodic task to find documents without summaries and generate them.
    
    This task scans the database for documents that don't have a summary field
    in their metadata and queues them for summary generation.
    
    Args:
        batch_size: Maximum number of documents to process in one batch
        
    Returns:
        Dictionary with status information
    """
    db = get_database()
    try:
        logger.info("Starting catchup task for document summaries")
        
        # Get all documents
        all_documents = db.get_all_documents()
        
        # Filter for documents without summaries
        docs_without_summary = [
            doc for doc in all_documents 
            if not (hasattr(doc.metadata, "summary") and doc.metadata.summary)
        ]
        
        # Limit to batch size
        batch = docs_without_summary[:batch_size]
        
        if not batch:
            logger.info("No documents found that need summaries")
            return {"status": "success", "processed": 0, "message": "No documents need summaries"}
            
        # Process each document
        logger.info(f"Found {len(batch)} documents that need summaries. Processing...")
        
        for doc in batch:
            # Call the summary task for each document with low priority
            # Priority 9 is typically the lowest for Celery with Redis
            generate_summary_task.apply_async(args=[doc.model_dump()], priority=9)
        
        logger.info(f"Dispatched {len(batch)} low priority summary tasks from catchup job.")
        
        return {
            "status": "success",
            "processed": len(batch),
            "total_pending": len(docs_without_summary),
            "message": f"Processed {len(batch)} of {len(docs_without_summary)} documents needing summaries"
        }
        
    except Exception as e:
        logger.error(f"Catchup summaries task failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
