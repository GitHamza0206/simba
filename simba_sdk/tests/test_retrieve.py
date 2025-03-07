import pytest
import responses
import requests
import json
from unittest.mock import MagicMock, patch
from simba_sdk import SimbaClient, RetrieveManager
from requests.exceptions import HTTPError, ConnectionError
from responses.matchers import json_params_matcher


class TestRetrieveManager:
    """Tests for the RetrieveManager class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock SimbaClient."""
        client = MagicMock(spec=SimbaClient)
        client.api_url = "https://api.simba.example.com"
        client.headers = {"Content-Type": "application/json", "Authorization": "Bearer fake-token"}
        return client
    
    @pytest.fixture
    def retrieve_manager(self, mock_client):
        """Create a RetrieveManager with a mock client."""
        return RetrieveManager(mock_client)
        
    @responses.activate
    def test_get_retrieval_strategies_success(self, retrieve_manager):
        """Test successfully getting retrieval strategies."""
        # Mock response data
        strategies = {
            "strategies": {
                "default": "Default retrieval strategy",
                "semantic": "Semantic search using embeddings",
                "keyword": "Keyword-based search",
                "hybrid": "Hybrid search combining approaches",
                "ensemble": "Ensemble search with multiple retrievers",
                "reranked": "Search with reranking"
            }
        }
        
        # Setup mock response
        responses.add(
            responses.GET,
            f"{retrieve_manager.client.api_url}/retriever/strategies",
            json=strategies,
            status=200
        )
        
        # Call the method
        result = retrieve_manager.get_retrieval_strategies()
        
        # Assertions
        assert result == strategies
        assert "strategies" in result
        assert len(result["strategies"]) == 6
        assert "semantic" in result["strategies"]
        assert "keyword" in result["strategies"]
    
    @responses.activate
    def test_get_retrieval_strategies_error(self, retrieve_manager):
        """Test error handling when getting retrieval strategies."""
        # Setup mock error response
        responses.add(
            responses.GET,
            f"{retrieve_manager.client.api_url}/retriever/strategies",
            json={"error": "Internal server error"},
            status=500
        )
        
        # Expect the method to raise an exception
        with pytest.raises(HTTPError):
            retrieve_manager.get_retrieval_strategies()
    
    @responses.activate
    def test_get_retrieval_strategies_connection_error(self, retrieve_manager):
        """Test connection error handling when getting retrieval strategies."""
        # Setup mock to raise connection error
        responses.add(
            responses.GET,
            f"{retrieve_manager.client.api_url}/retriever/strategies",
            body=ConnectionError("Connection refused")
        )
        
        # Expect the method to raise an exception
        with pytest.raises(ConnectionError):
            retrieve_manager.get_retrieval_strategies()
    
    @responses.activate
    def test_retrieve_basic(self, retrieve_manager):
        """Test basic document retrieval."""
        # Mock response data
        mock_response = {
            "documents": [
                {
                    "page_content": "Sample document 1",
                    "metadata": {"id": "doc1", "source": "file1.txt"}
                },
                {
                    "page_content": "Sample document 2",
                    "metadata": {"id": "doc2", "source": "file2.txt"}
                }
            ]
        }
        
        # Setup mock response
        responses.add(
            responses.POST,
            f"{retrieve_manager.client.api_url}/retriever/retrieve",
            json=mock_response,
            status=200,
            match=[
                json_params_matcher({"query": "test query", "method": "default", "k": 5})
            ]
        )
        
        # Call the method with basic parameters
        result = retrieve_manager.retrieve(query="test query")
        
        # Assertions
        assert result == mock_response
        assert "documents" in result
        assert len(result["documents"]) == 2
        assert result["documents"][0]["page_content"] == "Sample document 1"
        assert result["documents"][1]["metadata"]["id"] == "doc2"
    
    @responses.activate
    def test_retrieve_with_all_parameters(self, retrieve_manager):
        """Test retrieval with all optional parameters specified."""
        # Mock response data
        mock_response = {
            "documents": [
                {
                    "page_content": "Sample document about AI",
                    "metadata": {"id": "doc1", "category": "AI"}
                }
            ]
        }
        
        # Expected request payload
        expected_payload = {
            "query": "AI concepts",
            "method": "semantic",
            "k": 10,
            "filter": {"category": "AI"},
            "score_threshold": 0.8
        }
        
        # Setup mock response
        responses.add(
            responses.POST,
            f"{retrieve_manager.client.api_url}/retriever/retrieve",
            json=mock_response,
            status=200,
            match=[json_params_matcher(expected_payload)]
        )
        
        # Call the method with all parameters
        result = retrieve_manager.retrieve(
            query="AI concepts",
            method="semantic",
            filter={"category": "AI"},
            k=10,
            score_threshold=0.8
        )
        
        # Assertions
        assert result == mock_response
        assert len(result["documents"]) == 1
        assert "AI" in result["documents"][0]["page_content"]
    
    @responses.activate
    def test_retrieve_empty_results(self, retrieve_manager):
        """Test retrieval with no matching documents."""
        # Mock empty response
        mock_response = {"documents": []}
        
        # Setup mock response
        responses.add(
            responses.POST,
            f"{retrieve_manager.client.api_url}/retriever/retrieve",
            json=mock_response,
            status=200
        )
        
        # Call the method
        result = retrieve_manager.retrieve(query="nonexistent query")
        
        # Assertions
        assert result == mock_response
        assert "documents" in result
        assert len(result["documents"]) == 0
    
    @responses.activate
    def test_retrieve_server_error(self, retrieve_manager):
        """Test error handling during retrieval."""
        # Setup mock error response
        responses.add(
            responses.POST,
            f"{retrieve_manager.client.api_url}/retriever/retrieve",
            json={"error": "Internal server error"},
            status=500
        )
        
        # Expect the method to raise an exception
        with pytest.raises(HTTPError):
            retrieve_manager.retrieve(query="test query")
    
    @responses.activate
    def test_retrieve_invalid_parameters(self, retrieve_manager):
        """Test retrieval with invalid parameters."""
        # Setup mock error response for invalid parameters
        responses.add(
            responses.POST,
            f"{retrieve_manager.client.api_url}/retriever/retrieve",
            json={"detail": "Validation error"},
            status=422
        )
        
        # Expect the method to raise an exception
        with pytest.raises(HTTPError):
            retrieve_manager.retrieve(query="test query", score_threshold=1.5)  # Invalid threshold
    
    @responses.activate
    def test_retrieve_connection_timeout(self, retrieve_manager):
        """Test timeout handling during retrieval."""
        # Setup mock to raise connection error
        responses.add(
            responses.POST,
            f"{retrieve_manager.client.api_url}/retriever/retrieve",
            body=ConnectionError("Connection timed out")
        )
        
        # Expect the method to raise an exception
        with pytest.raises(ConnectionError):
            retrieve_manager.retrieve(query="test query")
    
    def test_headers_property(self, retrieve_manager, mock_client):
        """Test that the headers property returns the client's headers."""
        # Set headers on the mock client
        mock_client.headers = {"Authorization": "Bearer test-token", "Custom-Header": "Value"}
        
        # Check that the headers property returns the client's headers
        assert retrieve_manager.headers == mock_client.headers
        assert retrieve_manager.headers["Authorization"] == "Bearer test-token"
        assert retrieve_manager.headers["Custom-Header"] == "Value"
    
    @patch.object(requests, 'post')
    def test_retrieve_request_formation(self, mock_post, retrieve_manager):
        """Test that the retrieve method forms the request correctly."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"documents": []}
        mock_post.return_value = mock_response
        
        # Call the method with various parameters
        retrieve_manager.retrieve(
            query="test query",
            method="hybrid",
            filter={"category": "test"},
            k=3,
            score_threshold=0.7
        )
        
        # Verify the correct URL and headers were used
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # The first positional argument should be the URL
        assert args[0] == f"{retrieve_manager.client.api_url}/retriever/retrieve"
        assert kwargs["headers"] == retrieve_manager.headers
        
        # Verify the payload contains the expected parameters
        payload = kwargs["json"]
        assert payload["query"] == "test query"
        assert payload["method"] == "hybrid"
        assert payload["k"] == 3
        assert payload["filter"] == {"category": "test"}
        assert payload["score_threshold"] == 0.7
    