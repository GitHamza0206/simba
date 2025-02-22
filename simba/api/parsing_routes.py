import logging
import os

from celery.app.control import Inspect
from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from fastapi import APIRouter, BackgroundTasks, HTTPException
from simba.models.simbadoc import SimbaDoc
from pydantic import BaseModel
from simba.tasks.parsing_tasks import celery, parse_docling_task



logger = logging.getLogger(__name__)
parsing = APIRouter()

db = get_database()

@parsing.get("/parsers")
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    return {"parsers": "docling"}

class ParseDocumentRequest(BaseModel):
    document_id: str
    parser: str

@parsing.post("/parse")
async def parse_document(request: ParseDocumentRequest):
    """Parse a document asynchronously"""
    try:
        logger.info(f"Received parse request: {request}")
        
        # Verify document exists first
        simbadoc: SimbaDoc = db.get_document(request.document_id)
        if not simbadoc:
            raise HTTPException(status_code=404, detail="Document not found")

        elif request.parser == "docling":
            task = parse_docling_task.delay(request.document_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported parser")

        return {"task_id": task.id, "status_url": f"parsing/tasks/{task.id}"}

    except Exception as e:
        logger.error(f"Error enqueuing task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@parsing.get("/parsing/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Check status of a parsing task"""
    result = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }

@parsing.get("/parsing/tasks")
async def get_all_tasks():
    """Get all Celery tasks (active, reserved, scheduled)"""
    try:
        i = Inspect(app=celery)
        tasks = {
            'active': i.active(),  # Currently executing tasks
            'reserved': i.reserved(),  # Tasks that have been claimed by workers
            'scheduled': i.scheduled(),  # Tasks scheduled for later execution
            'registered': i.registered()  # All tasks registered in the worker
        }
        
        # Add task queue length if available
        try:
            stats = celery.control.inspect().stats()
            if stats:
                tasks['stats'] = stats
        except:
            pass
            
        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
