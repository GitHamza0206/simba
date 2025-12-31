"""Document management routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from simba.models import Collection, Document, get_db
from simba.services import ingestion_service, parser_service, qdrant_service, storage_service
from simba.tasks import process_document

router = APIRouter(prefix="/documents")


# --- Schemas ---


class DocumentResponse(BaseModel):
    id: str
    name: str
    collection_id: str
    collection_name: str
    status: str
    size_bytes: int
    mime_type: str
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    id: str
    name: str
    status: str
    message: str


class DocumentStatusItem(BaseModel):
    id: str
    status: str


class DocumentStatusResponse(BaseModel):
    items: list[DocumentStatusItem]
    has_processing: bool


# --- Routes ---


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    collection_id: str | None = Query(None, description="Filter by collection ID"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all documents with optional filtering."""
    query = db.query(Document)

    if collection_id:
        query = query.filter(Document.collection_id == collection_id)
    if status:
        query = query.filter(Document.status == status)

    total = query.count()
    documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    items = [
        DocumentResponse(
            id=doc.id,
            name=doc.name,
            collection_id=doc.collection_id,
            collection_name=doc.collection.name,
            status=doc.status,
            size_bytes=doc.size_bytes,
            mime_type=doc.mime_type,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]

    return DocumentListResponse(items=items, total=total)


@router.get("/status", response_model=DocumentStatusResponse)
async def get_documents_status(
    collection_id: str | None = Query(None, description="Filter by collection ID"),
    db: Session = Depends(get_db),
):
    """Lightweight endpoint to check document statuses (for polling)."""
    query = db.query(Document.id, Document.status)

    if collection_id:
        query = query.filter(Document.collection_id == collection_id)

    results = query.all()

    items = [DocumentStatusItem(id=r.id, status=r.status) for r in results]
    has_processing = any(r.status in ("pending", "processing") for r in results)

    return DocumentStatusResponse(items=items, has_processing=has_processing)


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: str = Query(..., description="Collection ID to upload to"),
    db: Session = Depends(get_db),
):
    """Upload a new document and queue it for processing."""
    # Validate collection exists
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Validate file type
    mime_type = file.content_type or "application/octet-stream"
    if not parser_service.is_supported_mime_type(mime_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {mime_type}. Supported types: {parser_service.get_supported_mime_types()}",
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Generate document ID and object key
    document_id = str(uuid4())
    filename = file.filename or "document"
    object_key = f"documents/{document_id}/{filename}"

    # Upload to MinIO
    storage_service.upload_file(file_content, object_key, mime_type)

    # Create document record
    document = Document(
        id=document_id,
        name=filename,
        collection_id=collection_id,
        status="pending",
        mime_type=mime_type,
        size_bytes=file_size,
        chunk_count=0,
        object_key=object_key,
    )
    db.add(document)
    db.commit()

    # Queue Celery task for processing
    process_document.delay(document_id)

    return DocumentUploadResponse(
        id=document_id,
        name=filename,
        status="pending",
        message="Document uploaded and queued for processing",
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document details."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=document.id,
        name=document.name,
        collection_id=document.collection_id,
        collection_name=document.collection.name,
        status=document.status,
        size_bytes=document.size_bytes,
        mime_type=document.mime_type,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its associated vectors."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    collection_name = document.collection.name

    # Delete from MinIO
    try:
        storage_service.delete_file(document.object_key)
    except Exception:
        pass  # File might not exist

    # Delete vectors from Qdrant
    try:
        ingestion_service.delete_document_vectors(document_id, collection_name)
    except Exception:
        pass  # Vectors might not exist

    # Delete from database
    db.delete(document)
    db.commit()

    return {"deleted": True, "id": document_id}


@router.post("/{document_id}/reprocess")
async def reprocess_document(document_id: str, db: Session = Depends(get_db)):
    """Reprocess a failed document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status not in ["failed", "ready"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reprocess document in status: {document.status}",
        )

    # Delete existing vectors
    try:
        collection_name = document.collection.name
        ingestion_service.delete_document_vectors(document_id, collection_name)
    except Exception:
        pass

    # Reset status and queue for processing
    document.status = "pending"
    document.chunk_count = 0
    document.error_message = None
    db.commit()

    process_document.delay(document_id)

    return {"status": "pending", "document_id": document_id, "message": "Document queued for reprocessing"}


@router.get("/{document_id}/download")
async def get_document_download_url(document_id: str, db: Session = Depends(get_db)):
    """Get a presigned URL for downloading the document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    url = storage_service.get_presigned_url(document.object_key)

    return {"download_url": url, "filename": document.name}


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str, db: Session = Depends(get_db)):
    """Get all chunks for a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not ready (status: {document.status})",
        )

    collection_name = document.collection.name
    chunks = qdrant_service.get_document_chunks(collection_name, document_id)

    return {
        "document_id": document_id,
        "document_name": document.name,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
