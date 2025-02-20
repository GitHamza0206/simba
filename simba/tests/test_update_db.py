import json
import logging
import sqlite3
import uuid

import MetadataType
import pytest
import SimbaDoc
from core.factories.database_factory import get_database
from database.litedb_service import LiteDocumentDB
from langchain_core.documents import Document
from models.simbadoc import SimbaDoc

logger = logging.getLogger(__name__)

@pytest.fixture
def db():
    """Get the actual database instance"""
    db = get_database()
    # Clean up any existing test documents
    try:
        db.clear_database()
    except Exception as e:
        logger.warning(f"Failed to clear database: {e}")
    return db

@pytest.fixture
def test_doc():
    """Create a test document with unique ID"""
    unique_id = f"test-doc-{uuid.uuid4()}"
    return SimbaDoc(
        id=unique_id,
        documents=[
            Document(
                page_content="test content",
                metadata={"chunk_id": "chunk-1"}
            )
        ],
        metadata=MetadataType(
            enabled=False,
            file_path="/test/path",
            filename="test.pdf",
            type="pdf"
        )
    )

def test_update_db(db, test_doc):
    """Test basic document update"""
    # Insert initial document
    db.insert_documents([test_doc])
    #db.refresh()
    
    # Update document enabled status
    updated_doc = test_doc.model_copy()
    updated_doc.metadata.enabled = True
    db.update_document(test_doc.id, updated_doc)
    #db.refresh()
    
    # Verify update
    retrieved_doc = db.get_document(test_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled == True
    
    # Cleanup
    db.delete_documents([test_doc.id])

def test_update_nonexistent_document(db):
    """Test updating a nonexistent document"""
    with pytest.raises(Exception):
        db.update_document("nonexistent-id", {"enabled": True})

def test_update_multiple_fields(db, test_doc):
    """Test updating multiple metadata fields"""
    # Insert document
    db.insert_documents([test_doc])
    db.refresh()
    
    # Update multiple fields
    updated_doc = test_doc.model_copy()
    updated_doc.metadata.enabled = True
    updated_doc.metadata.filename = "updated.pdf"
    updated_doc.metadata.file_path = "/new/path"
    
    db.update_document(test_doc.id, updated_doc)
    db.refresh()
    
    # Verify all updates
    retrieved_doc = db.get_document(test_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled == True
    assert retrieved_doc.metadata.filename == "updated.pdf"
    assert retrieved_doc.metadata.file_path == "/new/path"
    
    # Cleanup
    db.delete_documents([test_doc.id])

def test_update_and_revert(db, test_doc):
    """Test updating and reverting document state"""
    # Insert document
    db.insert_documents([test_doc])
    db.refresh()
    
    # Update enabled to True
    updated_doc = test_doc.model_copy()
    updated_doc.metadata.enabled = True
    db.update_document(test_doc.id, updated_doc)
    db.refresh()
    
    retrieved_doc = db.get_document(test_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled == True
    
    # Revert back to False
    updated_doc.metadata.enabled = False
    db.update_document(test_doc.id, updated_doc)
    db.refresh()
    
    retrieved_doc = db.get_document(test_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled == False
    
    # Cleanup
    db.delete_documents([test_doc.id])

def test_update_document_content(db, test_doc):
    """Test updating document content"""
    # Insert document
    db.insert_documents([test_doc])
    db.refresh()
    
    # Create new document with updated content
    updated_doc = test_doc.model_copy()
    updated_doc.documents[0].page_content = "updated content"
    
    # Update document
    db.update_document(test_doc.id, updated_doc)
    db.refresh()
    
    # Verify content update
    retrieved_doc = db.get_document(test_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.documents[0].page_content == "updated content"
    
    # Cleanup
    db.delete_documents([test_doc.id])

def test_bulk_document_updates(db):
    """Test updating multiple documents"""
    # Create multiple test documents with unique IDs
    docs = [
        SimbaDoc(
            id=f"test-doc-{uuid.uuid4()}",
            documents=[Document(page_content=f"content {i}", metadata={})],
            metadata=MetadataType(enabled=False)
        )
        for i in range(3)
    ]
    
    # Insert documents
    db.insert_documents(docs)
    db.refresh()
    
    # Update all documents
    for doc in docs:
        updated_doc = doc.model_copy()
        updated_doc.metadata.enabled = True
        db.update_document(doc.id, updated_doc)
    db.refresh()
    
    # Verify all updates
    for doc in docs:
        retrieved_doc = db.get_document(doc.id)
        assert retrieved_doc is not None
        assert retrieved_doc.metadata.enabled == True
    
    # Cleanup
    db.delete_documents([doc.id for doc in docs])

@pytest.mark.skip(reason="Only run manually for performance testing")
def test_update_performance(db, test_doc):
    """Test update performance with multiple operations"""
    import time

    # Insert document
    db.insert_documents([test_doc])
    db.refresh()
    
    # Measure update performance
    start_time = time.time()
    for _ in range(100):
        updated_doc = test_doc.model_copy()
        updated_doc.metadata.enabled = not updated_doc.metadata.enabled
        db.update_document(test_doc.id, updated_doc)
        db.refresh()
    
    duration = time.time() - start_time
    logger.info(f"100 update cycles completed in {duration:.2f} seconds")
    
    # Cleanup
    db.delete_documents([test_doc.id])

