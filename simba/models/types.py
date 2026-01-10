"""Shared SQLAlchemy column types."""

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


class StringListType(TypeDecorator):
    """Store list of strings across database backends."""

    cache_ok = True
    impl = JSON

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        return dialect.type_descriptor(JSON())
