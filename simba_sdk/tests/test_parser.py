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
    
    @responses.activate
    def test_extract_tables_sync(self, mock_client):
        """Test extracting tables from a document synchronously."""
        # Setup the mock response
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse/sync",
            json={
                "status": "success",
                "document_id": "doc123",
                "result": {
                    "document_id": "doc123",
                    "tables": [
                        {
                            "page": 1,
                            "table_id": "t1",
                            "data": [["Header1", "Header2"], ["Value1", "Value2"]]
                        }
                    ]
                }
            },
            status=200,
            match=[responses.matchers.query_param_matcher({"document_id": "doc123", "feature": "tables"})]
        )
        
        # Create parser manager and call the method
        parser = ParserManager(mock_client)
        result = parser.extract_tables("doc123", sync=True)
        
        # Check the result
        assert result["document_id"] == "doc123"
        assert result["result"]["document_id"] == "doc123"
        assert len(result["result"]["tables"]) == 1
        assert result["result"]["tables"][0]["page"] == 1
        assert result["result"]["tables"][0]["data"][0][0] == "Header1"
    
    @responses.activate
    def test_extract_tables_async(self, mock_client):
        """Test extracting tables from a document asynchronously."""
        # Setup the mock responses
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse",
            json={"task_id": "task123", "status_url": "parsing/tasks/task123"},
            status=200,
            match=[responses.matchers.json_params_matcher({"document_id": "doc123", "parser": "docling", "sync": False, "feature": "tables"})]
        )
        
        # Create parser manager and call the method
        parser = ParserManager(mock_client)
        result = parser.extract_tables("doc123", sync=False)
        
        # Check the result
        assert "task_id" in result
        assert result["task_id"] == "task123"
        assert "status_url" in result
    
    @responses.activate
    def test_extract_entities(self, mock_client):
        """Test extracting entities from a document."""
        # Setup the mock response
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse/sync",
            json={
                "status": "success",
                "document_id": "doc123",
                "result": {
                    "document_id": "doc123",
                    "entities": [
                        {"type": "person", "text": "John Doe", "page": 1, "confidence": 0.95},
                        {"type": "organization", "text": "Acme Inc", "page": 2, "confidence": 0.88}
                    ]
                }
            },
            status=200,
            match=[responses.matchers.query_param_matcher({"document_id": "doc123", "feature": "entities"})]
        )
        
        # Create parser manager and call the method
        parser = ParserManager(mock_client)
        result = parser.extract_entities("doc123")
        
        # Check the result
        assert result["document_id"] == "doc123"
        assert len(result["result"]["entities"]) == 2
        assert result["result"]["entities"][0]["type"] == "person"
        assert result["result"]["entities"][1]["text"] == "Acme Inc"
    
    @responses.activate
    def test_extract_forms(self, mock_client):
        """Test extracting form fields from a document."""
        # Setup the mock response
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse/sync",
            json={
                "status": "success",
                "document_id": "doc123",
                "result": {
                    "document_id": "doc123",
                    "form_fields": [
                        {"name": "full_name", "value": "John Doe"},
                        {"name": "email", "value": "john@example.com"}
                    ]
                }
            },
            status=200,
            match=[responses.matchers.query_param_matcher({"document_id": "doc123", "feature": "forms", "form_type": "application"})]
        )
        
        # Create parser manager and call the method
        parser = ParserManager(mock_client)
        result = parser.extract_forms("doc123", form_type="application")
        
        # Check the result
        assert result["document_id"] == "doc123"
        assert len(result["result"]["form_fields"]) == 2
        assert result["result"]["form_fields"][0]["name"] == "full_name"
        assert result["result"]["form_fields"][1]["value"] == "john@example.com"
    
    @responses.activate
    def test_extract_text(self, mock_client):
        """Test extracting text content from a document."""
        # Setup the mock response
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse/sync",
            json={
                "status": "success",
                "document_id": "doc123",
                "result": {
                    "document_id": "doc123",
                    "text": "This is the extracted text content.",
                    "sections": [
                        {"title": "Introduction", "content": "This is the introduction."},
                        {"title": "Conclusion", "content": "This is the conclusion."}
                    ]
                }
            },
            status=200,
            match=[responses.matchers.query_param_matcher({
                "document_id": "doc123", 
                "feature": "text", 
                "structured": "true", 
                "include_layout": "true"
            })]
        )
        
        # Create parser manager and call the method
        parser = ParserManager(mock_client)
        result = parser.extract_text("doc123", structured=True, include_layout=True)
        
        # Check the result
        assert result["document_id"] == "doc123"
        assert "text" in result["result"]
        assert len(result["result"]["sections"]) == 2
    
    @responses.activate
    def test_parse_query(self, mock_client):
        """Test extracting information based on a natural language query."""
        # Setup the mock response
        responses.add(
            responses.POST,
            "https://api.simba.example.com/parse/sync",
            json={
                "status": "success",
                "document_id": "doc123",
                "result": {
                    "document_id": "doc123",
                    "query_results": {"total_revenue": "$1,250,000"}
                }
            },
            status=200,
            match=[responses.matchers.query_param_matcher({
                "document_id": "doc123", 
                "feature": "query", 
                "query": "What is the total revenue?"
            })]
        )
        
        # Create parser manager and call the method
        parser = ParserManager(mock_client)
        result = parser.parse_query("doc123", "What is the total revenue?")
        
        # Check the result
        assert result["document_id"] == "doc123"
        assert result["query"] == "What is the total revenue?"
        assert result["result"]["query_results"]["total_revenue"] == "$1,250,000" 