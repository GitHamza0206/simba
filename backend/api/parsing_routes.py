from core.factories.database_factory import get_database
from fastapi import APIRouter, HTTPException
from models.simbadoc import SimbaDoc

from services.parser_service import ParserService
from pydantic import BaseModel
import logging
import os

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
    """Parse a document"""
    try:
        logger.info(f"Received parse request: {request}")
        
        simbadoc: SimbaDoc = db.get_document(request.document_id)
        # to Langchain documents

        
        parsed_document = parser_service.parse_document(simbadoc, request.parser)
        return parsed_document
    
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
