from unittest.mock import Mock, patch

import MetadataType
import pytest
import SimbaDoc
from langchain.schema import Document
from models.simbadoc import SimbaDoc
from services.ingestion_service.document_ingestion_service import (
    DocumentIngestionService,
)


@pytest.fixture
def mock_vector_store():
    mock = Mock()
    # Set up chunk_in_store method
    mock.chunk_in_store = Mock()
    return mock

@pytest.fixture
def mock_database():
    return Mock()

@pytest.fixture
def ingestion_service(mock_vector_store, mock_database):
    service = DocumentIngestionService()
    service.vector_store = mock_vector_store
    service.database = mock_database
    return service

def test_sync_with_store_enable_document(ingestion_service):
    """Test enabling document when chunks exist in store"""
    # Setup
    chunk1 = Document(page_content="test1", metadata={})
    chunk1.id = "chunk1"
    chunk2 = Document(page_content="test2", metadata={})
    chunk2.id = "chunk2"
    
    metadata = MetadataType(enabled=False)  # Start disabled
    simba_doc = SimbaDoc(
        id="doc1",
        documents=[chunk1, chunk2],
        metadata=metadata
    )
    
    # Configure mocks
    ingestion_service.database.get_all_documents.return_value = [simba_doc]
    ingestion_service.vector_store.chunk_in_store.side_effect = lambda x: True  # Chunks exist
    
    # Execute
    ingestion_service.sync_with_store()
    
    # Assert
    assert simba_doc.metadata.enabled == True
    ingestion_service.database.update_document.assert_called_once_with("doc1", simba_doc)

def test_sync_with_store_disable_document(ingestion_service):
    """Test disabling document when chunks don't exist in store"""
    # Setup
    chunk1 = Document(page_content="test1", metadata={})
    chunk1.id = "chunk1"
    
    metadata = MetadataType(enabled=True)  # Start enabled
    simba_doc = SimbaDoc(
        id="doc1",
        documents=[chunk1],
        metadata=metadata
    )
    
    # Configure mocks
    ingestion_service.database.get_all_documents.return_value = [simba_doc]
    ingestion_service.vector_store.chunk_in_store.side_effect = lambda x: False  # Chunks don't exist
    
    # Execute
    ingestion_service.sync_with_store()
    
    # Assert
    assert simba_doc.metadata.enabled == False
    ingestion_service.database.update_document.assert_called_once_with("doc1", simba_doc)

def test_sync_with_store_no_change_needed(ingestion_service):
    """Test no update when store state matches enabled status"""
    # Setup
    chunk1 = Document(page_content="test1", metadata={})
    chunk1.id = "chunk1"
    
    metadata = MetadataType(enabled=True)
    simba_doc = SimbaDoc(
        id="doc1",
        documents=[chunk1],
        metadata=metadata
    )
    
    # Configure mocks
    ingestion_service.database.get_all_documents.return_value = [simba_doc]
    ingestion_service.vector_store.chunk_in_store.side_effect = lambda x: True  # Matches enabled status
    
    # Execute
    ingestion_service.sync_with_store()
    
    # Assert
    assert simba_doc.metadata.enabled == True
    ingestion_service.database.update_document.assert_not_called()

def test_sync_with_store_error_handling(ingestion_service):
    """Test error handling during sync"""
    # Setup
    ingestion_service.database.get_all_documents.side_effect = Exception("Database error")
    
    # Execute & Assert
    with pytest.raises(Exception) as exc_info:
        ingestion_service.sync_with_store()
    assert str(exc_info.value) == "Database error" 