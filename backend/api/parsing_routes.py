from fastapi import APIRouter, HTTPException
from services.vector_store_service import VectorStoreService
from services.parser_service import ParserService
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)
parsing = APIRouter()

@parsing.get("/parsers")
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    parser_service = ParserService()
    parsers = parser_service.get_parsers()
    return {"parsers": parsers}

class ParseDocumentRequest(BaseModel):
    document_id: str
    parser: str

@parsing.post("/parse")
async def parse_document(request: ParseDocumentRequest):
    """Parse a document"""
    try:
        logger.info(f"Received parse request: {request}")
        
        vector_store = VectorStoreService()
        document = vector_store.get_document(request.document_id)
        
        parser_service = ParserService()
        parsed_document = parser_service.parse_document(document, request.parser)
        
        return parsed_document
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
