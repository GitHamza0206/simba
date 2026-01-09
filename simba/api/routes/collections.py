"""Collection management routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from simba.api.middleware.auth import OrganizationContext, get_current_org
from simba.models import Collection, Document, get_db
from simba.services import qdrant_service, storage_service

router = APIRouter(prefix="/collections")


# --- Schemas ---


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CollectionListResponse(BaseModel):
    items: list[CollectionResponse]
    total: int


def get_qdrant_collection_name(org_id: str, collection_name: str) -> str:
    """Generate Qdrant collection name with org namespace."""
    return f"{org_id}_{collection_name}"


# --- Routes ---


@router.get("", response_model=CollectionListResponse)
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    org: OrganizationContext = Depends(get_current_org),
):
    """List all collections for the current organization."""
    total = db.query(Collection).filter(Collection.organization_id == org.organization_id).count()
    collections = (
        db.query(Collection)
        .filter(Collection.organization_id == org.organization_id)
        .order_by(Collection.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        CollectionResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            document_count=c.document_count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in collections
    ]

    return CollectionListResponse(items=items, total=total)


@router.post("", response_model=CollectionResponse)
async def create_collection(
    data: CollectionCreate,
    db: Session = Depends(get_db),
    org: OrganizationContext = Depends(get_current_org),
):
    """Create a new collection for the current organization."""
    # Check if collection name already exists for this organization
    existing = (
        db.query(Collection)
        .filter(
            Collection.organization_id == org.organization_id,
            Collection.name == data.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Collection with this name already exists")

    # Create collection in database
    collection = Collection(
        id=str(uuid4()),
        organization_id=org.organization_id,
        name=data.name,
        description=data.description,
        document_count=0,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)

    # Create corresponding Qdrant collection with org namespace
    qdrant_collection_name = get_qdrant_collection_name(org.organization_id, data.name)
    qdrant_service.create_collection(qdrant_collection_name)

    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        document_count=collection.document_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    org: OrganizationContext = Depends(get_current_org),
):
    """Get collection details."""
    collection = (
        db.query(Collection)
        .filter(
            Collection.id == collection_id,
            Collection.organization_id == org.organization_id,
        )
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        document_count=collection.document_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    org: OrganizationContext = Depends(get_current_org),
):
    """Delete a collection and all its documents."""
    collection = (
        db.query(Collection)
        .filter(
            Collection.id == collection_id,
            Collection.organization_id == org.organization_id,
        )
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Delete all document files from MinIO
    documents = db.query(Document).filter(Document.collection_id == collection_id).all()
    for doc in documents:
        try:
            storage_service.delete_file(doc.object_key)
        except Exception:
            pass

    # Delete Qdrant collection with org namespace
    try:
        qdrant_collection_name = get_qdrant_collection_name(org.organization_id, collection.name)
        qdrant_service.delete_collection(qdrant_collection_name)
    except Exception:
        pass

    # Delete from database (cascade will delete documents)
    db.delete(collection)
    db.commit()

    return {"deleted": True, "id": collection_id}


@router.get("/{collection_id}/stats")
async def get_collection_stats(
    collection_id: str,
    db: Session = Depends(get_db),
    org: OrganizationContext = Depends(get_current_org),
):
    """Get collection statistics including vector count."""
    collection = (
        db.query(Collection)
        .filter(
            Collection.id == collection_id,
            Collection.organization_id == org.organization_id,
        )
        .first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get document stats
    total_docs = db.query(Document).filter(Document.collection_id == collection_id).count()
    ready_docs = (
        db.query(Document)
        .filter(Document.collection_id == collection_id, Document.status == "ready")
        .count()
    )
    failed_docs = (
        db.query(Document)
        .filter(Document.collection_id == collection_id, Document.status == "failed")
        .count()
    )
    processing_docs = (
        db.query(Document)
        .filter(Document.collection_id == collection_id, Document.status == "processing")
        .count()
    )

    # Get Qdrant stats with org namespace
    qdrant_info = None
    try:
        qdrant_collection_name = get_qdrant_collection_name(org.organization_id, collection.name)
        if qdrant_service.collection_exists(qdrant_collection_name):
            qdrant_info = qdrant_service.get_collection_info(qdrant_collection_name)
    except Exception:
        pass

    return {
        "collection_id": collection_id,
        "collection_name": collection.name,
        "documents": {
            "total": total_docs,
            "ready": ready_docs,
            "failed": failed_docs,
            "processing": processing_docs,
        },
        "vectors": qdrant_info,
    }
