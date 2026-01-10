"""Eval models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from simba.models.base import Base
from simba.models.types import StringListType


class EvalItem(Base):
    """Eval item model - represents a single evaluation entry."""

    __tablename__ = "eval_items"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[list[str] | None] = mapped_column(StringListType(), nullable=True)
    sources_groundtruth: Mapped[list[str] | None] = mapped_column(StringListType(), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    conversation_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_groundtruth: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieval_precision: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieval_recall: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    faithfulness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<EvalItem(id={self.id}, question={self.question[:50]}...)>"
