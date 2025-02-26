import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from tinydb import Query, TinyDB

from simba.core.config import settings
from simba.models.simbadoc import SimbaDoc

logger = logging.getLogger(__name__)


class TinyDocumentDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TinyDocumentDB, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the TinyDB connection"""
        try:
            db_path = (
                Path(settings.paths.upload_dir) / "documents.json"
            )  # TODO: make that configurable
            self.db = TinyDB(db_path)
            self.docs_table = self.db.table("documents")
            logger.info(f"Initialized TinyDB at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize TinyDB: {e}")
            raise

    def insert_anything(self, anything: Any) -> str:
        """Insert a new document into TinyDB"""
        try:
            doc_id = self.docs_table.insert(anything)
            return str(doc_id)
        except Exception as e:
            logger.error(f"Failed to insert document: {e}")
            raise

    def insert_documents(self, documents: SimbaDoc | List[SimbaDoc]) -> str:
        """Insert a new document into TinyDB"""
        try:
            doc_id = self.docs_table.insert(documents)
            return str(doc_id)
        except Exception as e:
            logger.error(f"Failed to insert document: {e}")
            raise

    def get_document(self, document_id: str) -> Optional[SimbaDoc]:
        """Retrieve a document by ID from TinyDB"""
        try:
            Doc = Query()
            return self.docs_table.get(Doc.id == document_id)
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    def get_all_documents(self) -> List[SimbaDoc]:
        """Retrieve all documents from TinyDB"""
        try:
            documents = self.docs_table.all()
            return documents
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []

    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID from TinyDB"""
        try:
            Doc = Query()
            self.docs_table.remove(Doc.id == document_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document by ID in TinyDB"""
        try:
            Doc = Query()
            self.docs_table.update(updates, Doc.id == document_id)
            return True
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            return False


if __name__ == "__main__":
    pass
