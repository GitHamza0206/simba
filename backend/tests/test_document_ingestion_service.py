import pytest
from unittest.mock import Mock, patch
from langchain.schema import Document
from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from services.ingestion_service.types import SimbaDoc, MetadataType

@pytest.fixture
def mock_vector_store():
    return Mock()

@pytest.fixture
def mock_database():
    return Mock()

@pytest.fixture
def ingestion_service(mock_vector_store, mock_database):
    service = DocumentIngestionService()
    service.vector_store = mock_vector_store
    service.database = mock_database
    return service

def test_sync_with_store_enabled_doc_not_in_store(ingestion_service):
    """Test when enabled SimbaDoc is not found in store"""
    # Setup
    metadata = MetadataType(enabled=True)
    mock_simba_doc = SimbaDoc(
        id="test_id",
        documents=[Document(page_content="test")],
        metadata=metadata
    )
    
    ingestion_service.database.get_all_documents.return_value = [mock_simba_doc]
    ingestion_service.vector_store.get_documents.return_value = []
    
    # Execute
    ingestion_service.sync_with_store()
    
    # Assert
    mock_simba_doc.metadata.enabled = False
    ingestion_service.database.update_document.assert_called_once_with(
        "test_id", 
        mock_simba_doc
    )

def test_sync_with_store_disabled_doc_in_store(ingestion_service):
    """Test when disabled SimbaDoc is found in store"""
    # Setup
    metadata = MetadataType(enabled=False)
    mock_simba_doc = SimbaDoc(
        id="test_id",
        documents=[Document(page_content="test")],
        metadata=metadata
    )
    
    store_doc = Document(
        page_content="test",
        metadata={"doc_id": "test_id"}
    )
    
    ingestion_service.database.get_all_documents.return_value = [mock_simba_doc]
    ingestion_service.vector_store.get_documents.return_value = [store_doc]
    
    # Execute
    ingestion_service.sync_with_store()
    
    # Assert
    mock_simba_doc.metadata.enabled = True
    ingestion_service.database.update_document.assert_called_once_with(
        "test_id", 
        mock_simba_doc
    )

def test_sync_with_store_no_changes_needed(ingestion_service):
    """Test when documents are already in sync"""
    # Setup
    metadata = MetadataType(enabled=True)
    mock_simba_doc = SimbaDoc(
        id="test_id",
        documents=[Document(page_content="test")],
        metadata=metadata
    )
    
    store_doc = Document(
        page_content="test",
        metadata={"doc_id": "test_id"}
    )
    
    ingestion_service.database.get_all_documents.return_value = [mock_simba_doc]
    ingestion_service.vector_store.get_documents.return_value = [store_doc]
    
    # Execute
    ingestion_service.sync_with_store()
    
    # Assert
    ingestion_service.database.update_document.assert_not_called()

def test_sync_with_store_error_handling(ingestion_service):
    """Test error handling during sync"""
    # Setup
    ingestion_service.database.get_all_documents.side_effect = Exception("Database error")
    
    # Execute & Assert
    with pytest.raises(Exception) as exc_info:
        ingestion_service.sync_with_store()
    assert str(exc_info.value) == "Database error" 