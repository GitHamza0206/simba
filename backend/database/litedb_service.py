import sqlite3
import json
from pathlib import Path
import logging
from typing import Dict, List, Optional, Any, cast
from core.config import settings
from services.ingestion_service.types import SimbaDoc

logger = logging.getLogger(__name__)

class LiteDocumentDB():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiteDocumentDB, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the database"""
        try:
            db_path = Path(settings.paths.upload_dir) / "documents.db"
            self.conn = sqlite3.connect(str(db_path))
            # Enable JSON serialization
            self.conn.row_factory = sqlite3.Row
            
            # Create table with a single JSON column
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS documents
                (id TEXT PRIMARY KEY, data JSON)
            ''')
            self.conn.commit()
            logger.info(f"Initialized LiteDB at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize LiteDB: {e}")
            raise

    def insert_documents(self, documents: SimbaDoc | List[SimbaDoc]) -> List[str]:
        """Insert one or multiple documents"""
        try:
            if not isinstance(documents, list):
                documents = [documents]
            
            cursor = self.conn.cursor()
            for doc in documents:
                cursor.execute(
                    'INSERT INTO documents (id, data) VALUES (?, ?)',
                    (doc.id, json.dumps(doc.dict()))
                )
            
            self.conn.commit()
            return [doc.id for doc in documents]
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to insert documents: {e}")
            raise

    def get_document(self, document_id: str) -> Optional[SimbaDoc]:
        """Retrieve a document by ID"""
        try:
            cursor = self.conn.cursor()
            result = cursor.execute(
                'SELECT data FROM documents WHERE id = ?', 
                (document_id,)
            ).fetchone()
            
            if result:
                return SimbaDoc(**json.loads(result[0]))
            return None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None

    def get_all_documents(self) -> List[SimbaDoc]:
        """Retrieve all documents"""
        try:
            cursor = self.conn.cursor()
            results = cursor.execute('SELECT data FROM documents').fetchall()
            return [SimbaDoc(**json.loads(row[0])) for row in results]
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        try:
            cursor = self.conn.cursor()
            # Create placeholders for the IN clause
            placeholders = ','.join(['?' for _ in document_ids])
            cursor.execute(
                f'DELETE FROM documents WHERE id IN ({placeholders})', 
                document_ids
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete documents {document_ids}: {e}")
            return False

    def update_document(self, document_id: str, newDocument: SimbaDoc) -> bool:
        """Update a document by ID"""
        try:
            # Get existing document
            doc = self.get_document(document_id)
            if not doc:
                return False
                
            # Update document
            doc_dict = doc.dict()
            doc_dict.update(newDocument.dict()) 
            
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE documents SET data = ? WHERE id = ?',
                (json.dumps(doc_dict), document_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update document {document_id}: {e}")
            return False

    def clear_database(self):
        """Clear the database"""
        try:
            self.conn.execute('DELETE FROM documents')
            self.conn.commit()
            logger.info("Database cleared") 
            return True
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return e
        


if __name__ == "__main__":
    db = LiteDocumentDB()
    from langchain_core.documents import Document
    from services.ingestion_service.types import MetadataType
    
    # # Test single document
    # doc1 = SimbaDoc(
    #     id='1',
    #     documents=[Document(page_content='test1')],
    #     metadata=MetadataType(file_name='test1.txt')
    # )
    
    # # Test multiple documents
    # docs = [
    #     SimbaDoc(
    #         id='2',
    #         documents=[Document(page_content='test2')],
    #         metadata=MetadataType(file_name='test2.txt')
    #     ),
    #     SimbaDoc(
    #         id='3',
    #         documents=[Document(page_content='test3')],
    #         metadata=MetadataType(file_name='test3.txt')
    #     )
    # ]
    
    # Insert and test
    alldocs = db.get_all_documents()
    for doc in alldocs:
        simbadoc = cast(SimbaDoc, doc)
        print(simbadoc.id)

        print(simbadoc.metadata)
        break
    #print("All documents:", alldocs) 