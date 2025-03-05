import pytest
import responses
import json
import time
from unittest.mock import MagicMock, patch
from simba_sdk import SimbaClient, ParserManager


class TestParserManager:
    """Tests for the ParserManager class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock SimbaClient."""
        client = MagicMock(spec=SimbaClient)
        client.api_url = "https://api.simba.example.com"
        client.headers = {"Content-Type": "application/json", "Authorization": "Bearer fake-token"}
        client._make_request = MagicMock()
        return client
    
    @pytest.fixture
    def parser_manager(self, mock_client):
        """Create a ParserManager with a mock client."""
        return ParserManager(mock_client)
    
    def test_get_parsers(self, mock_client, parser_manager):
        """Test getting available parsers."""
        # Setup mock return value
        mock_client._make_request.return_value = {"parsers": "docling"}
        
        # Call the method
        result = parser_manager.get_parsers()
        
        # Check result
        assert result == {"parsers": "docling"}
        mock_client._make_request.assert_called_once_with("GET", "parsers")
    
    @responses.activate
    def test_parse_document_sync(self, mock_client):
        """Test parsing a document synchronously."""
        # Setup the mock response for synchronous parsing
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse/sync",
            json={
                "status": "success",
                "document_id": "doc123",
                "result": {
                    "document_id": "doc123",
                    "num_chunks": 5,
                    "parsing_status": "SUCCESS",
                    "parsed_at": "2023-06-15T12:34:56.789012"
                }
            },
            status=200,
            match=[responses.matchers.query_param_matcher({"document_id": "doc123"})]
        )
        
        # Create parser manager and call the method with sync=True (default)
        parser = ParserManager(mock_client)
        result = parser.parse_document("doc123")
        
        # Check the result
        assert result["status"] == "success"
        assert result["document_id"] == "doc123"
        assert result["result"]["num_chunks"] == 5
        assert result["result"]["parsing_status"] == "SUCCESS"
        
        # Check that the request was made correctly
        assert len(responses.calls) == 1
        assert "document_id=doc123" in responses.calls[0].request.url
        
        # We no longer send the document_id in the body
        # Verify there's no payload in the body for synchronous parsing
        assert responses.calls[0].request.body in (None, b'')
    
    @responses.activate
    def test_parse_document_async(self, mock_client):
        """Test parsing a document asynchronously."""
        # Setup the mock response for asynchronous parsing
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse",
            json={"task_id": "task123", "status_url": "parsing/tasks/task123"},
            status=200
        )
        
        # Create parser manager and call the method with sync=False
        parser = ParserManager(mock_client)
        result = parser.parse_document("doc123", sync=False)
        
        # Check the result
        assert result["task_id"] == "task123"
        assert result["status_url"] == "parsing/tasks/task123"
        
        # Check that the request was made correctly
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://api.simba.example.com/parse"
        
        # Verify the payload
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["document_id"] == "doc123"
        assert request_body["parser"] == "docling"
        assert request_body["sync"] == False
    
    @responses.activate
    def test_parse_document_with_wait(self, mock_client):
        """Test parsing a document asynchronously and waiting for completion."""
        # Setup the mock response for initial parse request
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse",
            json={"task_id": "task123", "status_url": "parsing/tasks/task123"},
            status=200
        )
        
        # Setup the mock response for task status check
        responses.add(
            responses.GET,
            "https://api.simba.example.com/parsing/tasks/task123",
            json={
                "task_id": "task123", 
                "status": "SUCCESS",
                "result": {
                    "document_id": "doc123",
                    "parsed_data": {"title": "Test Document"}
                }
            },
            status=200
        )
        
        # Create parser manager and call the method with sync=False, wait_for_completion=True
        parser = ParserManager(mock_client)
        result = parser.parse_document("doc123", sync=False, wait_for_completion=True, 
                                      polling_interval=0.1, timeout=1)
        
        # Check the result
        assert result["task_id"] == "task123"
        assert result["status"] == "SUCCESS"
        assert result["result"]["document_id"] == "doc123"
        
        # Check that the requests were made correctly
        assert len(responses.calls) >= 2
        assert responses.calls[0].request.url == "https://api.simba.example.com/parse"
        assert responses.calls[1].request.url == "https://api.simba.example.com/parsing/tasks/task123"
    
    @responses.activate
    def test_get_task_status(self, mock_client, parser_manager):
        """Test getting status of a parsing task."""
        # Setup the mock response
        responses.add(
            responses.GET,
            "https://api.simba.example.com/parsing/tasks/task123",
            json={"task_id": "task123", "status": "PENDING"},
            status=200
        )
        
        # Call the method
        result = parser_manager.get_task_status("task123")
        
        # Check result
        assert result["task_id"] == "task123"
        assert result["status"] == "PENDING"
        
        # Check request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://api.simba.example.com/parsing/tasks/task123"
    
    @responses.activate
    def test_get_all_tasks(self, mock_client, parser_manager):
        """Test getting all parsing tasks."""
        # Setup the mock response
        responses.add(
            responses.GET,
            "https://api.simba.example.com/parsing/tasks",
            json={
                "active": {"worker1": [{"id": "task123", "name": "parse_docling_task"}]},
                "scheduled": {},
                "reserved": {}
            },
            status=200
        )
        
        # Call the method
        result = parser_manager.get_all_tasks()
        
        # Check result
        assert "active" in result
        assert "worker1" in result["active"]
        
        # Check request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://api.simba.example.com/parsing/tasks"
    
    