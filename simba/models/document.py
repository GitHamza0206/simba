"""Document and Collection models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from simba.models.base import Base


class Collection(Base):
    """Collection model - groups related documents."""

    __tablename__ = "collections"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_collection_org_name"),
        Index("idx_collections_org_id", "organization_id"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )  # References Better Auth organization table
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="collection", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name={self.name}, org={self.organization_id})>"


class Document(Base):
    """Document model - represents an uploaded file."""

    __tablename__ = "documents"
    __table_args__ = (Index("idx_documents_org_id", "organization_id"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    organization_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )  # Denormalized for query efficiency
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    collection_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("collections.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending, processing, ready, failed
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO object key
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name={self.name}, status={self.status})>"
