import os
import pytest
import json
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import responses
from io import BytesIO

from simba_sdk import SimbaClient, DocumentManager


@pytest.fixture
def client():
    """Create a test client with a mock API URL."""
    return SimbaClient(api_url="https://test-api.simba.com", api_key="test-key")


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test file for document upload tests."""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text("This is a test document for Simba SDK testing.")
    return file_path


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
    
    @responses.activate
    def test_create_document(self, client, test_file):
        """Test creating a document from a file path."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://test-api.simba.com/ingestion",
            json={"doc_id": "doc123", "status": "success"},
            status=200,
        )

        # Call the method
        response = client.documents.create(test_file)

        # Verify response
        assert response["doc_id"] == "doc123"
        assert response["status"] == "success"

        # Verify request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://test-api.simba.com/ingestion"
        # Check that Authorization header is present (don't check for Content-Type missing)
        assert "Authorization" in responses.calls[0].request.headers
        # For multipart form data, Content-Type will be present 
        # assert "Content-Type" not in responses.calls[0].request.headers

    @responses.activate
    def test_create_document_with_metadata(self, client, test_file):
        """Test creating a document with metadata."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://test-api.simba.com/ingestion",
            json={"doc_id": "doc123", "status": "success"},
            status=200,
        )

        # Call the method with metadata
        metadata = {"author": "Test User", "category": "testing"}
        response = client.documents.create(test_file, metadata=metadata)

        # Verify response
        assert response["doc_id"] == "doc123"
        
        # Verify request - check for metadata in the request
        assert len(responses.calls) == 1
        request_body = responses.calls[0].request.body
        # Since this is a multipart form, we need to check that the metadata is part of it
        assert b'name="metadata"' in request_body
        assert b'"author": "Test User"' in request_body
        assert b'"category": "testing"' in request_body

    @responses.activate
    def test_create_from_text(self, client):
        """Test creating a document from text."""
        # Mock the API response
        responses.add(
            responses.POST,
            "https://test-api.simba.com/ingestion",
            json={"doc_id": "doc456", "status": "success"},
            status=200,
        )

        # Call the method
        text = "This is a test document created from text."
        response = client.documents.create_from_text(text, "test_text_doc")

        # Verify response
        assert response["doc_id"] == "doc456"
        assert response["status"] == "success"

        # Verify a file was sent
        assert len(responses.calls) == 1
        assert b"This is a test document created from text" in responses.calls[0].request.body

    @responses.activate
    def test_get_document(self, client):
        """Test retrieving a document by ID."""
        doc_id = "doc123"
        # Mock the API response
        responses.add(
            responses.GET,
            f"https://test-api.simba.com/ingestion/{doc_id}",
            json={"doc_id": doc_id, "name": "test_document.txt", "metadata": {}},
            status=200,
        )

        # Call the method
        response = client.documents.get(doc_id)

        # Verify response
        assert response["doc_id"] == doc_id
        assert response["name"] == "test_document.txt"

        # Verify request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f"https://test-api.simba.com/ingestion/{doc_id}"
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test-key"

    @responses.activate
    def test_list_documents(self, client):
        """Test listing documents."""
        # Mock the API response
        responses.add(
            responses.GET,
            "https://test-api.simba.com/ingestion",
            json={"documents": [{"doc_id": "doc1"}, {"doc_id": "doc2"}], "total": 2},
            status=200,
        )

        # Call the method
        response = client.documents.list()

        # Verify response
        assert "documents" in response
        assert len(response["documents"]) == 2
        assert response["total"] == 2

        # Verify request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://test-api.simba.com/ingestion"

    @responses.activate
    def test_update_document(self, client):
        """Test updating a document's metadata."""
        doc_id = "doc123"
        # Mock the get response (needed for the update)
        responses.add(
            responses.GET,
            f"https://test-api.simba.com/ingestion/{doc_id}",
            json={"doc_id": doc_id, "name": "test_document.txt", "metadata": {"author": "Original Author"}},
            status=200,
        )
        
        # Mock the update response
        responses.add(
            responses.PUT,
            "https://test-api.simba.com/ingestion/update_document",
            json={"doc_id": doc_id, "status": "success"},
            status=200,
        )

        # Call the method
        new_metadata = {"author": "Updated Author", "status": "reviewed"}
        response = client.documents.update(doc_id, metadata=new_metadata)

        # Verify response
        assert response["doc_id"] == doc_id
        assert response["status"] == "success"

        # Verify request - check that both requests were made
        assert len(responses.calls) == 2
        # Check that the second request (PUT) contains the updated metadata
        update_request = responses.calls[1].request
        update_body = json.loads(update_request.body)
        assert update_body["metadata"]["author"] == "Updated Author"
        assert update_body["metadata"]["status"] == "reviewed"

    @responses.activate
    def test_delete_document(self, client):
        """Test deleting a document."""
        doc_id = "doc123"
        # Mock the API response
        responses.add(
            responses.DELETE,
            "https://test-api.simba.com/ingestion",
            json={"status": "success", "deleted": [doc_id]},
            status=200,
        )

        # Call the method
        response = client.documents.delete(doc_id)

        # Verify response
        assert response["status"] == "success"
        assert doc_id in response["deleted"]

        # Verify request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url.startswith("https://test-api.simba.com/ingestion")
        # Use the actual URL format instead of the expected format
        assert f"uids=doc123" in responses.calls[0].request.url

    @responses.activate
    def test_preview_document(self, client):
        """Test previewing a document."""
        doc_id = "doc123"
        preview_content = b"This is the document preview content"
        
        # Mock the API response
        responses.add(
            responses.GET,
            f"https://test-api.simba.com/preview/{doc_id}",
            body=preview_content,
            status=200,
        )

        # Call the method
        response = client.documents.preview(doc_id)

        # Verify response
        assert response == preview_content

        # Verify request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f"https://test-api.simba.com/preview/{doc_id}"
    
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
            "https://api.simba.example.com/ingestion",
            params={"uids": ["doc123"]},
            headers=document_manager.headers
        )

    @responses.activate
    def test_clear_db(self, client):
        """Test clearing the database."""
        # Mock the API response
        responses.add(
            responses.DELETE,
            "https://test-api.simba.com/db/clear",
            json={"status": "success", "message": "Database cleared"},
            status=200
        )
    
        # Call the method
        result = client.documents.clear_db()
        
        # Verify the result
        assert result["status"] == "success"
        assert result["message"] == "Database cleared"
    
    @patch("simba_sdk.simba_sdk.client.SimbaClient._make_request")
    def test_clear_db_with_mock(self, mock_make_request, document_manager):
        """Test clearing the database using mocks."""
        # Setup mock response
        mock_response = {"status": "success", "message": "Database cleared"}
        mock_make_request.return_value = mock_response
        
        # Replace the document_manager's client._make_request with our mock
        document_manager.client._make_request = mock_make_request
        
        # Call the method
        result = document_manager.clear_db()
        
        # Verify the result
        assert result == mock_response
        mock_make_request.assert_called_once_with(
            "DELETE",
            "/db/clear"
        ) 