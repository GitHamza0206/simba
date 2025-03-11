import json
import logging
import os

import torch
from celery.app.control import Inspect
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.embeddings import EmbeddingService
from simba.models.simbadoc import SimbaDoc
from simba.parsing.docling_parser import DoclingParser
from simba.parsing.mistral_ocr import MistralOCR
from simba.tasks.parsing_tasks import celery, parse_docling_task, parse_mistral_ocr_task

logger = logging.getLogger(__name__)
parsing = APIRouter()

db = get_database()
vector_store = VectorStoreFactory.get_vector_store()

PARSERS = {"docling": DoclingParser, "mistral_ocr": MistralOCR}


@parsing.get("/parsers")
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    parsers = list(PARSERS.keys())
    logger.info(f"Returning parsers: {parsers}")

    # Create a Response directly to prevent any transformation
    return JSONResponse(content={"parsers": parsers})


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

        # Handle synchronous parsing for any parser type
        if request.sync:

            logger.info(f"Processing synchronously with parser: {request.parser}")
            if request.parser == "docling":
                return await parse_document_sync(request.document_id, parser_type="docling")
            elif request.parser == "mistral_ocr":
                return await parse_document_sync(request.document_id, parser_type="mistral_ocr")
            else:
                raise HTTPException(status_code=400, detail="Unsupported parser")

        # Handle asynchronous parsing based on parser type
        if request.parser == "docling":
            logger.info(
                f"Starting asynchronous docling parsing for document: {request.document_id}"
            )
            task = parse_docling_task.delay(request.document_id)
            return {"task_id": task.id, "status_url": f"parsing/tasks/{task.id}"}
        elif request.parser == "mistral_ocr":
            logger.info(
                f"Starting asynchronous Mistral OCR parsing for document: {request.document_id}"
            )
            task = parse_mistral_ocr_task.delay(request.document_id)
            return {"task_id": task.id, "status_url": f"parsing/tasks/{task.id}"}
        else:
            logger.error(f"Unsupported parser: {request.parser}")
            raise HTTPException(status_code=400, detail=f"Unsupported parser: {request.parser}")

    except Exception as e:
        logger.error(f"Error processing parse request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@parsing.post("/parse/sync")
async def parse_document_sync(document_id: str, parser_type: str = "docling"):
    """Parse a document synchronously"""
    try:
        logger.info(
            f"Received synchronous parse request for document: {document_id} with parser: {parser_type}"
        )

        # Verify document exists first
        simbadoc: SimbaDoc = db.get_document(document_id)
        if not simbadoc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get parser
        if parser_type not in PARSERS:
            raise HTTPException(
                status_code=400,
                detail=f"Parser {parser_type} not found. Available parsers: {list(PARSERS.keys())}",
            )

        parser = PARSERS[parser_type]()

        # Parse document
        parsed_simba_doc = parser.parse(simbadoc)

        # Update database
        db.update_document(document_id, parsed_simba_doc)

        # Return the parsed document data
        return parsed_simba_doc
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
