from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import base64

from typing import List
from services.ingestion_service.config import SUPPORTED_EXTENSIONS
from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from services.parser_service import ParserService
from services.vector_store_service import VectorStoreService

from langchain_core.documents import Document


MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

ingestion = APIRouter()

@ingestion.delete("/ingestion")
async def delete_ingestion_documents(uid: str)->dict :
    ingestion_service = DocumentIngestionService()
    ingestion_service.delete_ingested_document(uid)
    return {"message": f"Document {uid} deleted successfully"}

@ingestion.get("/ingestion")
async def get_ingestion_documents():
    ingestion_service = DocumentIngestionService()
    ingested_documents = ingestion_service.get_ingested_documents()
    return ingested_documents

@ingestion.post("/ingestion")
async def ingest_document(file: UploadFile = File(...)):
    """Ingest documents into the vector store"""

    try:
        ingestion_service = DocumentIngestionService()
        result = ingestion_service.ingest_document(file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@ingestion.put("/document/{document_id}")
async def update_document(document_id: str, newDocument: Document):
    """Update the loader of a specific document"""
    ingestion_service = DocumentIngestionService()
    ingestion_service.update_document(document_id, newDocument)
    return {"message": f"Document {document_id} loader updated successfully"}   

#NOTE: This one should be written before the get_document_content endpoint because fastapi will match the first endpoint that matches the path
@ingestion.get("/loaders")
async def get_loaders():
    """Get the list of loaders supported by the document ingestion service"""
    loaders = [ loader.__name__ for loader in SUPPORTED_EXTENSIONS.values()]
    print(loaders)
    return {"loaders": loaders}

@ingestion.get("/document/{document_id}")
async def get_document_content(document_id: str):
    """Get the content of a specific document"""
    try:
        store = VectorStoreService()
        document = store.get_document(document_id)
        
        if not document:
            return JSONResponse(
                status_code=404,
                content={"message": "Document not found"}
            )
            
        # Get the original file path from metadata
        file_path = document.metadata.get('source')
        file_type = document.metadata.get('type', '').lower()
        
        # If it's a PDF, read and encode the binary content
        if file_type == 'pdf':
            with open(file_path, 'rb') as file:
                pdf_content = file.read()
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                return {
                    "content": pdf_base64,
                    "type": "pdf"
                }
        
        # For other file types, return the text content
        return {
            "content": document.page_content,
            "type": file_type
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": f"Error retrieving document: {str(e)}"}
        )

@ingestion.get("/parsers")
async def get_parsers():
    """Get the list of parsers supported by the document ingestion service"""
    parser_service = ParserService()
    parsers = parser_service.get_parsers()
    return {"parsers": parsers}



