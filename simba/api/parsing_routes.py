import logging

import torch
from celery.app.control import Inspect
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.models.simbadoc import SimbaDoc
from simba.parsing.docling_parser import DoclingParser
from simba.tasks.parsing_tasks import celery, parse_docling_task

logger = logging.getLogger(__name__)
parsing = APIRouter()

db = get_database()
vector_store = VectorStoreFactory.get_vector_store()


@parsing.get("/parsers")
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    return {"parsers": "docling"}


class ParseDocumentRequest(BaseModel):
    document_id: str
    parser: str
    sync: bool = False  # New parameter to indicate whether to parse synchronously


@parsing.post("/parse")
async def parse_document(request: ParseDocumentRequest):
    """Parse a document asynchronously or synchronously based on the sync parameter"""
    try:
        logger.info(f"Received parse request: {request}")

        # Verify document exists first
        simbadoc: SimbaDoc = db.get_document(request.document_id)
        if not simbadoc:
            raise HTTPException(status_code=404, detail="Document not found")

        # If sync is True, parse synchronously
        if request.sync:
            if request.parser == "docling":
                return await parse_document_sync(request.document_id)
            else:
                raise HTTPException(status_code=400, detail="Unsupported parser")

        # Otherwise, parse asynchronously using Celery
        elif request.parser == "docling":
            task = parse_docling_task.delay(request.document_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported parser")

        return {"task_id": task.id, "status_url": f"parsing/tasks/{task.id}"}

    except Exception as e:
        logger.error(f"Error processing parse request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@parsing.post("/parse/sync")
async def parse_document_sync(document_id: str):
    """Parse a document synchronously"""
    try:
        logger.info(f"Received synchronous parse request for document: {document_id}")

        # Verify document exists first
        simbadoc: SimbaDoc = db.get_document(document_id)
        if not simbadoc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Perform parsing directly
        try:
            parser = DoclingParser()
            parsed_simba_doc = parser.parse(simbadoc)

            # Update database
            vector_store.add_documents(parsed_simba_doc.documents)
            db.update_document(document_id, parsed_simba_doc)

            # Return the parsed document data
            return {
                "status": "success",
                "document_id": parsed_simba_doc.id,
                "result": {
                    "document_id": parsed_simba_doc.id,
                    "num_chunks": (
                        len(parsed_simba_doc.documents) if parsed_simba_doc.documents else 0
                    ),
                    "parsing_status": parsed_simba_doc.metadata.parsing_status,
                    "parsed_at": (
                        parsed_simba_doc.metadata.parsed_at.isoformat()
                        if parsed_simba_doc.metadata.parsed_at
                        else None
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}", exc_info=True)
            return {"status": "error", "document_id": document_id, "error": str(e)}
        finally:
            # Clean up any remaining GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    except Exception as e:
        logger.error(f"Error processing synchronous parse request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@parsing.get("/parsing/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Check status of a parsing task"""
    result = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }


@parsing.get("/parsing/tasks")
async def get_all_tasks():
    """Get all Celery tasks (active, reserved, scheduled)"""
    try:
        i = Inspect(app=celery)
        tasks = {
            "active": i.active(),  # Currently executing tasks
            "reserved": i.reserved(),  # Tasks that have been claimed by workers
            "scheduled": i.scheduled(),  # Tasks scheduled for later execution
            "registered": i.registered(),  # All tasks registered in the worker
        }

        # Add task queue length if available
        try:
            stats = celery.control.inspect().stats()
            if stats:
                tasks["stats"] = stats
        except Exception as e:
            logger.error(f"Error fetching tasks stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
