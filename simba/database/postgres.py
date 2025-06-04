import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from fastapi import HTTPException, status
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, String, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool
from datetime import datetime
import json

from simba.core.config import settings
from simba.models.simbadoc import SimbaDoc, MetadataType
from simba.database.base import DatabaseService
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

Base = declarative_base()

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that converts datetime objects to ISO format strings."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class SQLDocument(Base):
    """SQLAlchemy model for documents table"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    
    # Add relationship to chunks
    chunks = relationship("ChunkEmbedding", back_populates="document", cascade="all, delete-orphan")
    
    @classmethod
    def from_simbadoc(cls, doc: SimbaDoc, user_id: str) -> "SQLDocument":
        """Create Document from SimbaDoc with datetime handling"""
        return cls(
            id=doc.id,
            user_id=user_id,
            data=json.loads(json.dumps(doc.dict(), cls=DateTimeEncoder))
        )
    
    def to_simbadoc(self) -> SimbaDoc:
        """Convert to SimbaDoc"""
        return SimbaDoc(**self.data)

class PostgresDB(DatabaseService):
    """PostgreSQL database access with connection pooling and SQLAlchemy ORM."""
    
    # Connection pool singleton
    _pool = None
    _engine = None
    _Session = None
    
    def __init__(self):
        """Initialize database connection and ensure schema exists."""
        self._get_pool()
        self._initialize_sqlalchemy()
        self._ensure_schema()
    
    @classmethod
    def _get_pool(cls):
        """Get or create the connection pool."""
        if cls._pool is None:
            try:
                cls._pool = ThreadedConnectionPool(
                    minconn=3,
                    maxconn=10,
                    user=settings.postgres.user,
                    password=settings.postgres.password,
                    host=settings.postgres.host,
                    port=settings.postgres.port,
                    dbname=settings.postgres.db,
                    sslmode='require'
                )
                logger.info("Created PostgreSQL connection pool")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to connect to database"
                )
        return cls._pool
    
    def _initialize_sqlalchemy(self):
        """Initialize SQLAlchemy engine and session factory."""
        if self._engine is None:
            url = URL.create(
                "postgresql",
                username=settings.postgres.user,
                password=settings.postgres.password,
                host=settings.postgres.host,
                port=settings.postgres.port,
                database=settings.postgres.db
            )
            # Use NullPool since we're managing our own connection pool
            self._engine = create_engine(url, poolclass=NullPool)
            self._Session = sessionmaker(bind=self._engine)
            Base.metadata.create_all(self._engine)
            logger.info("Initialized SQLAlchemy engine")
    
    def _ensure_schema(self):
        """Ensure the required database schema exists."""
        Base.metadata.create_all(self._engine)
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool and return it when done."""
        pool = cls._get_pool()
        conn = None
        try:
            conn = pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        finally:
            if conn:
                pool.putconn(conn)
    
    # Raw SQL query methods
    @classmethod
    def execute_query(cls, query, params=None):
        """Run an INSERT, UPDATE, or DELETE query."""
        with cls.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    logger.info(f"Executing query: {query}")
                    logger.info(f"Parameters: {params}")
                    cursor.execute(query, params or ())
                    rowcount = cursor.rowcount
                    logger.info(f"Query executed successfully. Affected rows: {rowcount}")
                conn.commit()
                logger.info("Transaction committed")
                return rowcount
            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database query failed: {str(e)}"
                )
    
    @classmethod
    def fetch_all(cls, query, params=None):
        """Run a SELECT query and return all results."""
        with cls.get_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    logger.info(f"Executing fetch_all query: {query}")
                    logger.info(f"Parameters: {params}")
                    cursor.execute(query, params or ())
                    results = cursor.fetchall()
                    logger.info(f"Query returned {len(results)} results")
                    return [dict(row) for row in results]
            except Exception as e:
                logger.error(f"fetch_all error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database fetch failed: {str(e)}"
                )
    
    @classmethod
    def fetch_one(cls, query, params=None):
        """Run a SELECT query and return one result."""
        with cls.get_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    logger.info(f"Executing fetch_one query: {query}")
                    logger.info(f"Parameters: {params}")
                    cursor.execute(query, params or ())
                    row = cursor.fetchone()
                    if row:
                        logger.info(f"Query returned a row with id: {row.get('id')}")
                        return dict(row)
                    else:
                        logger.warning("Query returned no results")
                        return None
            except Exception as e:
                logger.error(f"fetch_one error: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database fetch failed: {str(e)}"
                )
    
    # ORM methods implementing DatabaseService interface
    def insert_document(self, document: SimbaDoc, user_id: str) -> str:
        """Insert a single document using SQLAlchemy ORM."""
        try:
            session = self._Session()
            db_doc = SQLDocument.from_simbadoc(document, user_id)
            session.add(db_doc)
            session.commit()
            return document.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert document: {e}")
            raise
        finally:
            session.close()
    
    def insert_documents(self, documents: SimbaDoc | List[SimbaDoc], user_id: str) -> List[str]:
        """Insert one or multiple documents using SQLAlchemy ORM."""
        if not isinstance(documents, list):
            documents = [documents]
            
        try:
            session = self._Session()
            db_docs = [SQLDocument.from_simbadoc(doc, user_id) for doc in documents]
            session.add_all(db_docs)
            session.commit()
            return [doc.id for doc in documents]
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert documents: {e}")
            raise
        finally:
            session.close()
    
    def get_document(self, document_id: str | List[str], user_id: str = None) -> Optional[SimbaDoc] | List[Optional[SimbaDoc]]:
        """Retrieve a document by ID or a list of documents by IDs using SQLAlchemy ORM.
        If a list of IDs is provided, returns a list of SimbaDoc (None for not found).
        If a single ID is provided, returns a single SimbaDoc or None.
        """
        try:
            session = self._Session()
            if isinstance(document_id, list):
                query = session.query(SQLDocument).filter(SQLDocument.id.in_(document_id))
                if user_id:
                    query = query.filter(SQLDocument.user_id == user_id)
                docs = query.all()
                # Map id to doc for fast lookup
                doc_map = {doc.id: doc for doc in docs}
                # Return in the same order as input list, None if not found
                return [doc_map.get(doc_id).to_simbadoc() if doc_map.get(doc_id) else None for doc_id in document_id]
            else:
                query = session.query(SQLDocument).filter(SQLDocument.id == document_id)
                if user_id:
                    query = query.filter(SQLDocument.user_id == user_id)
                doc = query.first()
                return doc.to_simbadoc() if doc else None
        except Exception as e:
            logger.error(f"Failed to get document(s) {document_id}: {e}")
            if isinstance(document_id, list):
                return [None for _ in document_id]
            return None
        finally:
            session.close()
    
    def get_all_documents(self, user_id: str = None) -> List[SimbaDoc]:
        """Retrieve all documents using SQLAlchemy ORM."""
        try:
            session = self._Session()
            query = session.query(SQLDocument)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(SQLDocument.user_id == user_id)
            
            docs = query.all()
            return [doc.to_simbadoc() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
        finally:
            session.close()
    
    def update_document(self, document_id: str, document: SimbaDoc, user_id: str = None) -> bool:
        """Update a document using SQLAlchemy ORM with proper datetime handling."""
        try:
            session = self._Session()
            # Convert to dict with datetime handling
            doc_dict = json.loads(json.dumps(document.dict(), cls=DateTimeEncoder))
            
            # Build query
            query = session.query(SQLDocument).filter(SQLDocument.id == document_id)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(SQLDocument.user_id == user_id)
            
            result = query.update({"data": doc_dict})
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update document {document_id}: {e}")
            return False
        finally:
            session.close()
    
    def delete_document(self, document_id: str, user_id: str = None) -> bool:
        """Delete a document using SQLAlchemy ORM."""
        try:
            session = self._Session()
            
            # Build query
            query = session.query(SQLDocument).filter(SQLDocument.id == document_id)
            
            # Filter by user_id if provided
            if user_id:
                query = query.filter(SQLDocument.user_id == user_id)
            
            result = query.delete()
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
        finally:
            session.close()
            
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete multiple documents using SQLAlchemy ORM."""
        try:
            session = self._Session()
            result = session.query(SQLDocument).filter(SQLDocument.id.in_(document_ids)).delete(synchronize_session=False)
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete documents: {e}")
            return False
        finally:
            session.close()
    
    def clear_database(self) -> bool:
        """Clear all documents from the database using SQLAlchemy ORM."""
        try:
            session = self._Session()
            session.query(SQLDocument).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to clear database: {e}")
            return False
        finally:
            session.close()
    
    def query_documents(self, filters: Dict[str, Any]) -> List[SimbaDoc]:
        """Query documents using filters.
        
        Supports filtering on both document ID and nested JSON data fields.
        For JSON data, use dot notation in filter keys, e.g.:
        {
            'id': '123',
            'user_id': 'user-uuid',
            'metadata.source': 'web',
            'content': 'search text'
        }
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            
        Returns:
            List of matching documents
        """
        try:
            session = self._Session()
            query = session.query(SQLDocument)
            
            for key, value in filters.items():
                if key == 'id':
                    query = query.filter(SQLDocument.id == value)
                elif key == 'user_id':
                    query = query.filter(SQLDocument.user_id == value)
                else:
                    # Handle nested JSON filters using PostgreSQL JSON operators
                    path_parts = key.split('.')
                    # Build the JSON path operator
                    json_path_str = '->'.join([f"'{part}'" for part in path_parts[:-1]])
                    if json_path_str:
                        json_path_str += '->>'
                    else:
                        json_path_str = '->>'
                    json_path_str += f"'{path_parts[-1]}'"
                    
                    # Apply the filter using raw SQL for JSON operators
                    query = query.filter(
                        f"data {json_path_str} = :value",
                        value=str(value)
                    )
            
            results = query.all()
            return [doc.to_simbadoc() for doc in results]
            
        except Exception as e:
            logger.error(f"Failed to query documents: {e}")
            return []
        finally:
            session.close()
    
    @classmethod
    def health_check(cls):
        """Test if database c   onnection works."""
        try:
            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
            
    @classmethod
    def close_pool(cls):
        """Close all connections in the pool."""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            logger.info("Closed PostgreSQL connection pool")

if __name__ == "__main__":
    from langchain.schema import Document as LangchainDocument
    db = PostgresDB()
    db.insert_documents(SimbaDoc(id="1", documents=[LangchainDocument(page_content="Hello, world!", metadata={"source": "test"})], metadata=MetadataType(filename="test")), "user-uuid")
    #print(db.delete_documents(["1"]))
    db.close_pool()
