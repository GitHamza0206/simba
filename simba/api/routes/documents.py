"""Document management routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4

router = APIRouter(prefix="/documents")


# --- Schemas ---


class DocumentResponse(BaseModel):
    id: str
    name: str
    status: str  # pending, parsing, ready, failed
    size_bytes: int
    mime_type: str
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class ChunkResponse(BaseModel):
    id: str
    content: str
    position: int
    metadata: dict


# --- Routes ---


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """List all documents."""
    # TODO: Implement actual document listing from DB
    return DocumentListResponse(items=[], total=0)


@router.post("", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a new document."""
    # TODO: Implement actual file upload and processing
    now = datetime.utcnow()
    return DocumentResponse(
        id=str(uuid4()),
        name=file.filename or "unknown",
        status="pending",
        size_bytes=0,
        mime_type=file.content_type or "application/octet-stream",
        created_at=now,
        updated_at=now,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document details."""
    # TODO: Implement actual document retrieval
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    # TODO: Implement actual document deletion
    return {"deleted": True, "id": document_id}


@router.post("/{document_id}/parse")
async def parse_document(document_id: str):
    """Trigger document parsing."""
    # TODO: Implement actual parsing (later with Celery)
    return {"status": "parsing", "document_id": document_id}


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(document_id: str):
    """Get document chunks."""
    # TODO: Implement actual chunk retrieval
    return []
