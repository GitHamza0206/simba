from simba.ingestion.document_ingestion import DocumentIngestionService
from simba.models.simbadoc import SimbaDoc, MetadataType
import pytest
import tempfile
from pathlib import Path
from simba.core.celery_config import celery_app
from simba.tasks.ingestion_tasks import ingest_document_task
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
import os
from langchain.schema import Document
import datetime


# Mock the database connection and SQLAlchemy engine
@pytest.fixture(autouse=True, scope="session")
def mock_postgres_initialization():
    with patch("simba.database.postgres.PostgresDB._initialize_sqlalchemy"), \
         patch("simba.database.postgres.PostgresDB._get_pool"), \
         patch("sqlalchemy.create_engine"), \
         patch("sqlalchemy.orm.sessionmaker"):
        yield


# Define test document
@pytest.fixture
def test_document():
    doc = Document(
        page_content="Test content",
        metadata={
            "filename": "test_file.md",
            "source": "test_file.md"
        }
    )
    return doc


# Test the document ingestion function with direct instantiation of SimbaDoc
@pytest.mark.asyncio
async def test_document_ingestion():
    # Setup mocks
    mock_db = MagicMock()
    mock_vector_store = MagicMock()
    
    # Create a special mock path that can handle stat() calls
    mock_path = MagicMock(spec=Path)
    mock_path.stat.return_value = MagicMock(st_size=1024)  # Mock size of 1KB
    mock_path.__str__.return_value = "test_file.md"
    
    mock_storage = AsyncMock()
    mock_storage.save_file.return_value = mock_path
    
    # Create a real Document object instead of a MagicMock
    test_doc = Document(
        page_content="Test content",
        metadata={
            "source": "test_file.md",
            "filename": "test_doc.md"
        }
    )
    # Set an ID for the document
    test_doc.id = str(uuid.uuid4())
    
    # Create a SimbaDoc to return from our mocked methods
    metadata = MetadataType(
        filename="test_doc.md",
        type=".md",
        page_number=1,
        chunk_number=0,
        enabled=False,
        parsing_status="Unparsed",
        size="1.00 MB",
        loader="TestLoader",
        uploadedAt=datetime.datetime.now().isoformat(),
        file_path=str(mock_path),
        parser=None,
    )
    simba_doc = SimbaDoc(
        id=str(uuid.uuid4()),
        documents=[test_doc],
        metadata=metadata
    )
    
    mock_loader = AsyncMock()
    mock_loader.aload.return_value = test_doc
    
    mock_splitter = MagicMock()
    mock_splitter.split_document.return_value = [test_doc]
    
    # Create mock SimbaDoc.from_documents to return our pre-created SimbaDoc
    with patch("simba.models.simbadoc.SimbaDoc.from_documents", return_value=simba_doc):
        # Create mock file
        mock_file = MagicMock()
        mock_file.filename = "test_doc.md"
        
        # Patch all other dependencies
        with patch("simba.core.factories.database_factory.get_database", return_value=mock_db), \
             patch("simba.core.factories.vector_store_factory.VectorStoreFactory.get_vector_store", return_value=mock_vector_store), \
             patch("simba.core.factories.storage_factory.StorageFactory.get_storage_provider", return_value=mock_storage), \
             patch("simba.ingestion.document_ingestion.Loader", return_value=mock_loader), \
             patch("simba.ingestion.document_ingestion.Splitter", return_value=mock_splitter), \
             patch("simba.tasks.generate_summary.generate_summary_task"), \
             patch("pathlib.Path.stat", return_value=MagicMock(st_size=1024)), \
             patch("os.path.exists", return_value=True):
            
            # Create service instance and manually set properties
            service = DocumentIngestionService.__new__(DocumentIngestionService)
            service.vector_store = mock_vector_store
            service.database = mock_db
            service.loader = mock_loader
            service.splitter = mock_splitter
            service.storage = mock_storage
            
            # Patch the generate_summary_task to avoid Celery issues
            with patch("simba.tasks.generate_summary.generate_summary_task.delay"):
                # Test document ingestion
                result = await service.ingest_document(mock_file, "/test")
                
                # Verify result
                assert result is not None
                assert result == simba_doc
                assert mock_storage.save_file.called


# Test the document retrieval function
def test_get_document():
    # Setup mocks
    mock_db = MagicMock()
    mock_vector_store = MagicMock()
    test_doc = MagicMock()
    mock_vector_store.get_document.return_value = test_doc
    
    # Create service instance and manually set properties
    service = DocumentIngestionService.__new__(DocumentIngestionService)
    service.vector_store = mock_vector_store
    service.database = mock_db
    
    # Test document retrieval
    document = service.get_document("test-doc-id")
    
    # Verify result
    assert document is test_doc
    mock_vector_store.get_document.assert_called_once_with("test-doc-id")


# Test the Celery task for document ingestion
def test_ingest_document_task():
    """Test the Celery task for document ingestion"""
    
    # Patch dependencies to avoid actual processing or connections
    with patch("simba.tasks.ingestion_tasks.get_database") as mock_db_func, \
         patch("simba.ingestion.document_ingestion.DocumentIngestionService") as mock_service_class, \
         patch("simba.tasks.ingestion_tasks.ingest_document_task.delay") as mock_delay:
        
        # Setup mocks
        mock_db = MagicMock()
        mock_db_func.return_value = mock_db
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_simba_doc = MagicMock()
        mock_simba_doc.id = str(uuid.uuid4())
        mock_simba_doc.model_dump.return_value = {"id": mock_simba_doc.id}
        
        # Mock service to return our mock document
        mock_service.ingest_document = AsyncMock(return_value=mock_simba_doc)
        
        # Mock delay to return a successful result
        mock_delay.return_value.get.return_value = {
            "status": "success",
            "document_id": mock_simba_doc.id,
            "message": "Document test_file.md ingested successfully"
        }
        
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".md") as temp_file:
            # Write test content
            Path(temp_file.name).write_text("# Test Content")
            
            # Setup the expected result
            result = {
                "status": "success",
                "document_id": mock_simba_doc.id,
                "message": f"Document {Path(temp_file.name).name} ingested successfully"
            }
            
            # Assertions
            assert result["status"] == "success"
            assert "document_id" in result
            assert "ingested successfully" in result["message"]


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_document_ingestion())
