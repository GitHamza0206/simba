import os
import uuid

import pytest
from langchain.schema import Document

from simba.core.config import settings
from simba.database.litedb_service import LiteDocumentDB
from simba.models.simbadoc import MetadataType, SimbaDoc


@pytest.fixture
def db():
    """Create a test database instance"""
    # Use a test-specific database file in memory
    os.path.join(settings.paths.data_dir, "test.db")
    return LiteDocumentDB()  # LiteDB uses settings for path


@pytest.fixture
def sample_doc():
    """Create a sample SimbaDoc"""
    doc_id = str(uuid.uuid4())
    metadata = MetadataType(
        enabled=True,
    )
    return SimbaDoc(
        id=doc_id,
        documents=[Document(id="1", page_content="test content", metadata={})],
        metadata=metadata,
    )


def test_update_document_enabled_status(db, sample_doc):
    """Test updating document enabled status"""
    # First insert the document
    db.insert_documents([sample_doc])

    # Update enabled status
    updated_doc = sample_doc.model_copy()
    updated_doc.metadata.enabled = False

    # Perform update
    result = db.update_document(sample_doc.id, updated_doc)
    assert result is True

    # Verify update
    retrieved_doc = db.get_document(sample_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled is False
    assert retrieved_doc.id == sample_doc.id


def test_update_nonexistent_document(db):
    """Test updating a document that doesn't exist"""
    fake_doc = SimbaDoc(id="nonexistent", documents=[], metadata=MetadataType(enabled=True))

    with pytest.raises(Exception):
        db.update_document("nonexistent", fake_doc)


def test_update_document_preserves_data(db, sample_doc):
    """Test that update preserves all document data"""
    # Insert original document
    db.insert_documents([sample_doc])

    # Modify multiple fields
    updated_doc = sample_doc.model_copy()
    updated_doc.metadata.enabled = False
    updated_doc.metadata.file_name = "updated.pdf"
    updated_doc.documents[0].page_content = "updated content"

    # Perform update
    result = db.update_document(sample_doc.id, updated_doc)
    assert result is True

    # Verify all fields were updated correctly
    retrieved_doc = db.get_document(sample_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled is False
    assert retrieved_doc.metadata.file_name == "updated.pdf"
    assert retrieved_doc.documents[0].page_content == "updated content"
    assert retrieved_doc.metadata.file_path == sample_doc.metadata.file_path  # Unchanged field


def test_update_document_with_refresh(db, sample_doc):
    """Test update with database refresh"""
    # Insert document
    db.insert_documents([sample_doc])

    # Update document
    updated_doc = sample_doc.model_copy()
    updated_doc.metadata.enabled = False

    # Perform update and refresh
    db.update_document(sample_doc.id, updated_doc)
    db.refresh()

    # Verify after refresh
    retrieved_doc = db.get_document(sample_doc.id)
    assert retrieved_doc is not None
    assert retrieved_doc.metadata.enabled is False


def test_multiple_updates(db, sample_doc):
    """Test multiple sequential updates to same document"""
    # Insert document
    db.insert_documents([sample_doc])

    # Perform multiple updates
    for i in range(3):
        updated_doc = sample_doc.model_copy()
        updated_doc.metadata.enabled = bool(i % 2)  # Toggle enabled
        updated_doc.metadata.file_name = f"test_{i}.pdf"

        result = db.update_document(sample_doc.id, updated_doc)
        assert result is True

        # Verify each update
        retrieved_doc = db.get_document(sample_doc.id)
        assert retrieved_doc is not None
        assert retrieved_doc.metadata.enabled == bool(i % 2)
        assert retrieved_doc.metadata.file_name == f"test_{i}.pdf"


def teardown_module(module):
    """Clean up after tests"""
    test_db_path = os.path.join(settings.paths.data_dir, "test.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
