import os
import pytest
import json
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from simba_sdk import SimbaClient, DocumentManager


class TestDocumentManager:
    """Tests for the DocumentManager class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock SimbaClient."""
        client = MagicMock(spec=SimbaClient)
        client.api_url = "https://api.simba.example.com"
        client.headers = {"Content-Type": "application/json", "Authorization": "Bearer fake-token"}
        return client
    
    @pytest.fixture
    def document_manager(self, mock_client):
        """Create a DocumentManager with a mock client."""
        return DocumentManager(mock_client)
    
    @patch("requests.post")
    def test_create(self, mock_post, document_manager):
        """Test creating a document from a file path."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"Test document content")
            tmp_path = tmp.name
        
        try:
            # Mock response
            mock_response = MagicMock()
            mock_response.json.return_value = {"document_id": "doc123", "status": "success"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Test with metadata
            metadata = {"author": "Test Author", "category": "Test"}
            result = document_manager.create(tmp_path, metadata)
            
            # Assertions
            assert result == {"document_id": "doc123", "status": "success"}
            mock_post.assert_called_once()
            
            # Check that the correct URL was used
            args, kwargs = mock_post.call_args
            assert args[0] == "https://api.simba.example.com/documents"
            
            # Check that metadata was included in the request
            assert 'metadata' in kwargs['data']
            assert json.loads(kwargs['data']['metadata']) == metadata
            
            # Check that file was included in the request
            assert 'file' in kwargs['files']
            
        finally:
            # Clean up
            os.unlink(tmp_path)
    
    @patch("requests.post")
    def test_create_file_not_found(self, mock_post, document_manager):
        """Test creating a document with a nonexistent file."""
        # Use a path that should not exist
        non_existent_path = "/path/to/nonexistent/file.pdf"
        
        # Test that FileNotFoundError is raised
        with pytest.raises(FileNotFoundError):
            document_manager.create(non_existent_path)
        
        # Verify that post was not called
        mock_post.assert_not_called()
    
    @patch("requests.post")
    def test_create_from_file(self, mock_post, document_manager):
        """Test creating a document from a file object."""
        # Mock file object
        mock_file = MagicMock()
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"document_id": "doc123", "status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test without metadata
        result = document_manager.create_from_file(mock_file, "test.pdf")
        
        # Assertions
        assert result == {"document_id": "doc123", "status": "success"}
        mock_post.assert_called_once()
        
        # Check that the correct URL was used
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.simba.example.com/documents"
        
        # Check that file was included in the request
        assert 'file' in kwargs['files']
        assert kwargs['files']['file'][0] == "test.pdf"
    
    @patch("requests.post")
    def test_create_from_text(self, mock_post, document_manager):
        """Test creating a document from text."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"document_id": "doc123", "status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        text = "This is a test document."
        name = "test-doc.txt"
        metadata = {"author": "Test Author"}
        
        # Call the method
        result = document_manager.create_from_text(text, name, metadata)
        
        # Assertions
        assert result == {"document_id": "doc123", "status": "success"}
        mock_post.assert_called_once()
        
        # Check that the correct URL was used
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.simba.example.com/documents/text"
        
        # Check that payload contains the correct data
        assert kwargs['json'] == {
            "text": text,
            "name": name,
            "metadata": metadata
        }
    
    @patch("requests.get")
    def test_get(self, mock_get, document_manager):
        """Test retrieving a document by ID."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "document_id": "doc123",
            "name": "test.pdf",
            "metadata": {"author": "Test Author"},
            "chunks": [{"id": "chunk1", "text": "Test chunk"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the method
        result = document_manager.get("doc123")
        
        # Assertions
        assert result["document_id"] == "doc123"
        assert result["chunks"][0]["text"] == "Test chunk"
        mock_get.assert_called_once_with(
            "https://api.simba.example.com/documents/doc123",
            headers=document_manager.headers
        )
    
    @patch("requests.get")
    def test_list(self, mock_get, document_manager):
        """Test listing documents."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"document_id": "doc123", "name": "test1.pdf"},
                {"document_id": "doc456", "name": "test2.pdf"}
            ],
            "total": 2,
            "page": 1,
            "page_size": 20
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the method with filters
        filters = {"author": "Test Author"}
        result = document_manager.list(page=2, page_size=10, filters=filters)
        
        # Assertions
        assert len(result["items"]) == 2
        assert result["items"][0]["document_id"] == "doc123"
        
        # Check that parameters were passed correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "https://api.simba.example.com/documents"
        assert kwargs["params"]["page"] == 2
        assert kwargs["params"]["page_size"] == 10
        assert json.loads(kwargs["params"]["filters"]) == filters
    
    @patch("requests.patch")
    def test_update(self, mock_patch, document_manager):
        """Test updating a document."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "document_id": "doc123",
            "status": "updated",
            "metadata": {"author": "New Author", "category": "Updated"}
        }
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response
        
        # Call the method
        metadata = {"author": "New Author", "category": "Updated"}
        result = document_manager.update("doc123", metadata)
        
        # Assertions
        assert result["status"] == "updated"
        assert result["metadata"]["author"] == "New Author"
        
        # Check the request
        mock_patch.assert_called_once_with(
            "https://api.simba.example.com/documents/doc123",
            json={"metadata": metadata},
            headers=document_manager.headers
        )
    
    @patch("requests.delete")
    def test_delete(self, mock_delete, document_manager):
        """Test deleting a document."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "document_id": "doc123",
            "status": "deleted"
        }
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        # Call the method
        result = document_manager.delete("doc123")
        
        # Assertions
        assert result["status"] == "deleted"
        mock_delete.assert_called_once_with(
            "https://api.simba.example.com/documents/doc123",
            headers=document_manager.headers
        ) 