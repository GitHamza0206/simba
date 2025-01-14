from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import base64

from typing import List
from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from services.vector_store_service import VectorStoreService


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
    # Validate file extension
    file_extension = f".{file.filename.split('.')[-1].lower()}"
    if file_extension not in DocumentIngestionService.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {list(DocumentIngestionService.SUPPORTED_EXTENSIONS.keys())}"
        )
    
    # Validate file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )
    
    # Reset file position for processing
    await file.seek(0)
    
    try:
        ingestion_service = DocumentIngestionService()
        result = ingestion_service.ingest_document(file)
        return {"message": f"File {file.filename} ingested successfully", "count": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

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


