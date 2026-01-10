"""SQLAlchemy base and database session management."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from simba.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def _create_engine() -> Engine:
    """Create a database engine with SQLite-safe defaults."""
    engine_options: dict[str, object] = {"echo": settings.debug}
    if settings.database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if settings.database_url.endswith(":memory:"):
            engine_options["poolclass"] = StaticPool
    return create_engine(settings.database_url, **engine_options)


# Database engine
engine = _create_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
