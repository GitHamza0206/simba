from fastapi import APIRouter, HTTPException
from services.ingestion_service.types import IngestedDocument
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
    file_path: str
    parser: str

@parsing.post("/parse")
async def parse_document(request: ParseDocumentRequest):
    """Parse a document"""
    try:
        logger.info(f"Received parse request: {request}")
        
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_path}"
            )
            
        parser_service = ParserService()
        parsed_document = parser_service.parse_document(request.file_path, request.parser)
        
        return {
            "parsed_document": {
                "file_path": os.path.splitext(request.file_path)[0] + '.md',
                "content": parsed_document
            }
        }
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
