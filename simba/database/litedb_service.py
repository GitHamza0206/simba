import atexit
import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from simba.core.config import settings
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.models.simbadoc import SimbaDoc

logger = logging.getLogger(__name__)


class LiteDocumentDB:
    def __init__(self):
        """Initialize the database"""
        self.db_path = Path(settings.paths.upload_dir) / "documents.db"
        self._conn = None
        self._initialize()
        atexit.register(self.close)

    def _initialize(self):
        """Initialize the database"""
        try:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            # Enable JSON serialization
            self._conn.row_factory = sqlite3.Row

            # Create table with a single JSON column
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents
                (id TEXT PRIMARY KEY, data JSON)
            """
            )
            self._conn.commit()
            logger.info(f"Initialized LiteDB at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LiteDB: {e}")
            raise

    @property
    def conn(self):
        """Get the database connection, creating a new one if needed"""
        if self._conn is None:
            self._initialize()
        return self._conn

    def close(self):
        """Close the database connection"""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._conn = None

    def insert_documents(self, documents: SimbaDoc | List[SimbaDoc]) -> List[str]:
        """Insert one or multiple documents"""
        try:
            if not isinstance(documents, list):
                documents = [documents]

            cursor = self.conn.cursor()
            for doc in documents:
                cursor.execute(
                    "INSERT INTO documents (id, data) VALUES (?, ?)",
                    (doc.id, json.dumps(doc.dict())),
                )

            self.conn.commit()
            return [doc.id for doc in documents]
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert documents: {e}")
            raise
        finally:
            cursor.close()

    def get_document(self, document_id: str) -> Optional[SimbaDoc]:
        """Retrieve a document by ID"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            logger.info(f"Fetching document with ID: {document_id}")

            result = cursor.execute(
                "SELECT data FROM documents WHERE id = ?", (document_id,)
            ).fetchone()

            if result:
                logger.info(f"Document found with ID: {document_id}")
                try:
                    doc_data = json.loads(result[0])
                    return SimbaDoc(**doc_data)
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse document data for ID {document_id}: {je}")
                    return None
            else:
                logger.warning(f"No document found with ID: {document_id}")
                return None

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            self._initialize()  # Re-initialize connection on error
            return None
        finally:
            if cursor:
                cursor.close()

    def get_all_documents(self) -> List[SimbaDoc]:
        """Retrieve all documents"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            results = cursor.execute("SELECT data FROM documents").fetchall()
            return [SimbaDoc(**json.loads(row[0])) for row in results]
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            placeholders = ",".join(["?" for _ in document_ids])
            cursor.execute(
                f"DELETE FROM documents WHERE id IN ({placeholders})",
                document_ids,
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Failed to delete documents {document_ids}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def update_document(self, document_id: str, newDocument: SimbaDoc) -> bool:
        """Update a document by ID"""
        cursor = None
        try:
            cursor = self.conn.cursor()

            # First check if document exists
            existing = cursor.execute(
                "SELECT 1 FROM documents WHERE id = ?", (document_id,)
            ).fetchone()

            if not existing:
                logger.warning(f"No document found with ID {document_id}")
                return False

            # Convert document to JSON, preserving all fields
            doc_json = newDocument.model_dump_json()

            # Update the document
            cursor.execute(
                "UPDATE documents SET data = ? WHERE id = ?",
                (doc_json, document_id),
            )

            # Force commit
            self.conn.commit()

            logger.info(f"Document {document_id} updated successfully")
            return True

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            logger.error(f"Failed to update document {document_id}: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()

    def clear_database(self):
        """Clear the database"""
        cursor = None
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM documents")
            self.conn.commit()
            logger.info("Database cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return e
        finally:
            if cursor:
                cursor.close()

    def sync_store(self):
        """Sync the database with the vector store by:
        1. Finding documents that exist in vector store but not in DB (to be deleted)
        2. Finding documents that exist in DB but not in vector store (to be added)
        3. Performing the necessary delete and add operations
        """
        try:
            # we should remove orphan chunks from vector store

            # Get all documents from DB
            documents = self.get_all_documents()
            db_document_ids = [doc.id for doc in documents]
            logger.info(f"Found {len(documents)} documents in database")

            # Get vector store
            vector_store = VectorStoreFactory.get_vector_store()
            all_embedded_docs = vector_store.get_documents()
            store_document_ids = [doc.id for doc in all_embedded_docs]

            # oprhan chunks
            orphan_chunks = set(store_document_ids) - set(db_document_ids)
            logger.info(f"Orphan chunks: {orphan_chunks}")
            logger.info(f"Found {len(orphan_chunks)} orphan chunks in vector store")

            # delete orphan chunks
            vector_store.delete_documents(list(orphan_chunks))
            logger.info(f"Deleted {len(orphan_chunks)} orphan chunks from vector store")

        except Exception as e:
            logger.error(f"Failed to sync database with vector store: {e}")
            raise
