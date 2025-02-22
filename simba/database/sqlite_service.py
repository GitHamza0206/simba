import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from simba.core.config import settings
from simba.models.simbadoc import SimbaDoc
from sqlalchemy import JSON, Column, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

# Separate SQLAlchemy model
class DocumentModel():
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True)
    documents = Column(JSON)
    metadata = Column(JSON)

    def to_simba_doc(self) -> SimbaDoc:
        """Convert to SimbaDoc"""
        return SimbaDoc(
            id=self.id,
            documents=self.documents,
            metadata=self.metadata
        )

    @classmethod
    def from_simba_doc(cls, doc: SimbaDoc) -> 'DocumentModel':
        """Create from SimbaDoc"""
        return cls(
            id=doc.id,
            documents=[d.dict() for d in doc.documents],
            metadata=doc.metadata.dict()
        )

class SQLiteDocumentDB():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SQLiteDocumentDB, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the SQLite database"""
        try:
            db_path = Path(settings.paths.upload_dir) / "documents.db"
            self.engine = create_engine(f'sqlite:///{db_path}')
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info(f"Initialized SQLite DB at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite DB: {e}")
            raise

    def insert_documents(self, documents: SimbaDoc | List[SimbaDoc]) -> List[str]:
        """Insert one or multiple documents"""
        try:
            session = self.Session()
            if not isinstance(documents, list):
                documents = [documents]
            
            db_docs = [DocumentModel.from_simba_doc(doc) for doc in documents]
            for doc in db_docs:
                session.add(doc)
            
            session.commit()
            return [doc.id for doc in documents]
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert documents: {e}")
            raise
        finally:
            session.close()

    def get_document(self, document_id: str) -> Optional[SimbaDoc]:
        """Retrieve a document by ID"""
        try:
            session = self.Session()
            doc = session.query(DocumentModel).filter_by(id=document_id).first()
            return doc.to_simba_doc() if doc else None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
        finally:
            session.close()

    def get_all_documents(self) -> List[SimbaDoc]:
        """Retrieve all documents"""
        try:
            session = self.Session()
            docs = session.query(DocumentModel).all()
            return [doc.to_simba_doc() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
        finally:
            session.close()

    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID"""
        try:
            session = self.Session()
            result = session.query(DocumentModel).filter_by(id=document_id).delete()
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
        finally:
            session.close()

    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document by ID"""
        try:
            session = self.Session()
            result = session.query(DocumentModel).filter_by(id=document_id).update(updates)
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update document {document_id}: {e}")
            return False
        finally:
            session.close()

