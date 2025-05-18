import logging
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from simba.tasks.generate_summary import generate_summary_task
from simba.core.factories.database_factory import get_database
from simba.models.simbadoc import SimbaDoc
from simba.core.celery_config import celery_app

logger = logging.getLogger(__name__)
summarize_router = APIRouter()
db = get_database()


class SummarizeDocumentRequest(BaseModel):
    document_id: str
    prioritize: bool = Field(default=False, description="Set to true to prioritize this summary task.")


@summarize_router.post("/summarize", status_code=202)
async def trigger_document_summary(request: SummarizeDocumentRequest):
    """
    Trigger summary generation for a document.
    """
    try:
        logger.info(f"Received summary request for document_id: {request.document_id}, prioritize: {request.prioritize}")

        # Verify document exists first
        simbadoc: SimbaDoc = db.get_document(request.document_id)
        if not simbadoc:
            logger.error(f"Document not found: {request.document_id} for summarization")
            raise HTTPException(status_code=404, detail="Document not found")

        # Dispatch the Celery task
        simbadoc_data = simbadoc.model_dump()
        
        if request.prioritize:
            # Priority 0 is typically the highest for Celery with Redis
            task = generate_summary_task.apply_async(args=[simbadoc_data], priority=0)
            logger.info(f"Dispatched HIGH PRIORITY summary task for document_id: {request.document_id}, task_id: {task.id}")
        else:
            # Default priority (e.g., 4 or Celery's default if not specified)
            # Using apply_async for consistency, can also use .delay()
            task = generate_summary_task.apply_async(args=[simbadoc_data], priority=4) # Assuming 4 is a standard/lower priority
            logger.info(f"Dispatched REGULAR PRIORITY summary task for document_id: {request.document_id}, task_id: {task.id}")
            
        return {"task_id": task.id, "status": "accepted", "message": "Summary generation initiated."}

    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        logger.error(f"Error processing summary request for document_id {request.document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# It might be useful to have a way to check summary task status, similar to parsing tasks.
# This would require the task ID to be stored or a way to query Celery results.
# For now, we'll just trigger the task. If status check is needed,
# a new endpoint /summarize/tasks/{task_id} could be added.

@summarize_router.get("/summarize/tasks/{task_id}")
async def get_summary_task_status(task_id: str):
    """
    Check the status of a summary generation task.
    """
    logger.info(f"Checking status for summary task_id: {task_id}")
    try:
        result = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "message": f"Status for task {task_id} is {result.status}"
        }
    except Exception as e:
        logger.error(f"Error checking status for task_id {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}") 