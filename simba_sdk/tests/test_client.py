import pytest
import requests
from unittest.mock import patch, MagicMock
from simba_sdk import SimbaClient

def test_client_initialization():
    """Test client initialization with and without API key."""
    # Test without API key
    client = SimbaClient("https://api.simba.com")
    assert client.api_url == "https://api.simba.com"
    assert client.api_key is None
    assert client.headers == {"Content-Type": "application/json"}
    
    # Test with API key
    client = SimbaClient("https://api.simba.com/", "test-key")
    assert client.api_url == "https://api.simba.com"  # Trailing slash removed
    assert client.api_key == "test-key"
    assert client.headers == {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-key"
    }
    
    # Test manager initialization
    assert hasattr(client, "documents")
    assert hasattr(client, "chat")
    assert hasattr(client, "parser")
    assert hasattr(client, "embedding")
    assert hasattr(client, "retriever")

@pytest.mark.parametrize("method,endpoint,params,json_data,form_data,files,stream,expected_url", [
    ("GET", "test", None, None, None, None, False, "https://api.simba.com/test"),
    ("POST", "/test", {"param": "value"}, None, None, None, False, "https://api.simba.com/test"),
    ("PUT", "test/", None, {"data": "value"}, None, None, False, "https://api.simba.com/test"),
    ("DELETE", "/test/", None, None, {"form": "data"}, None, False, "https://api.simba.com/test"),
])
def test_make_request(method, endpoint, params, json_data, form_data, files, stream, expected_url):
    """Test the _make_request method with various parameters."""
    client = SimbaClient("https://api.simba.com", "test-key")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_response.text = "success"
    mock_response.content = b"success"
    
    with patch("requests.request") as mock_request:
        mock_request.return_value = mock_response
        
        result = client._make_request(
            method=method,
            endpoint=endpoint,
            params=params,
            json=json_data,
            data=form_data,
            files=files,
            stream=stream
        )
        
        # Verify request was made correctly
        mock_request.assert_called_once_with(
            method,
            expected_url,
            params=params,
            json=json_data,
            data=form_data,
            files=files,
            headers=client.headers,
            stream=stream
        )
        
        # Verify response handling
        if stream:
            assert result == b"success"
        else:
            assert result == {"status": "success"}

def test_make_request_with_files():
    """Test _make_request when uploading files."""
    client = SimbaClient("https://api.simba.com", "test-key")
    files = {"file": ("test.txt", "content")}
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    
    with patch("requests.request") as mock_request:
        mock_request.return_value = mock_response
        
        client._make_request("POST", "upload", files=files)
        
        # Verify Content-Type was removed for file upload
        headers_used = mock_request.call_args[1]["headers"]
        assert "Content-Type" not in headers_used
        assert "Authorization" in headers_used

def test_make_request_error_handling():
    """Test error handling in _make_request."""
    client = SimbaClient("https://api.simba.com", "test-key")
    
    with patch("requests.request") as mock_request:
        # Test HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_request.return_value = mock_response
        
        with pytest.raises(requests.HTTPError):
            client._make_request("GET", "test")
        
        # Test JSON decode error
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Not JSON"
        mock_request.return_value = mock_response
        
        result = client._make_request("GET", "test")
        assert result == "Not JSON"  # Should return raw text when JSON parsing fails
