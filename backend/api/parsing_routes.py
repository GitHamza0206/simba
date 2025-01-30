from core.factories.database_factory import get_database
from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.simbadoc import SimbaDoc

from services.parser_service import ParserService
from pydantic import BaseModel
import logging
import os
from tasks.parsing_tasks import parse_markitdown_task, parse_docling_task
from core.config import settings

logger = logging.getLogger(__name__)
parsing = APIRouter()

parser_service = ParserService()
db = get_database()

@parsing.get("/parsers")
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    parsers = parser_service.get_parsers()
    return {"parsers": parsers}

class ParseDocumentRequest(BaseModel):
    document_id: str
    parser: str

@parsing.post("/parse")
async def parse_document(request: ParseDocumentRequest):
    """Parse a document asynchronously"""
    if not settings.features.enable_parsers:
        raise HTTPException(
            status_code=501, 
            detail="Document parsing is disabled in system configuration"
        )
    try:
        logger.info(f"Received parse request: {request}")
        
        # Verify document exists first
        simbadoc: SimbaDoc = db.get_document(request.document_id)
        if not simbadoc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Dispatch to Celery using document ID only
        if request.parser == "markitdown":
            task = parse_markitdown_task.delay(request.document_id)
        elif request.parser == "docling":
            task = parse_docling_task.delay(request.document_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported parser")

        return {"task_id": task.id, "status_url": f"parsing/tasks/{task.id}"}

    except Exception as e:
        logger.error(f"Error queuing parsing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@parsing.get("/parsing/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Check status of a parsing task"""
    from tasks.parsing_tasks import celery
    
    result = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
