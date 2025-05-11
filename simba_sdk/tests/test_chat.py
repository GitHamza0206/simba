import pytest
from unittest.mock import MagicMock
from simba_sdk import SimbaClient, ChatManager

@pytest.fixture
def client():
    """Create a test client with a mock API URL."""
    return SimbaClient(api_url="https://test-api.simba.com", api_key="test-key")

@pytest.fixture
def chat_manager(client):
    """Create a ChatManager instance with a mock client."""
    return ChatManager(client)

def test_chat_manager_initialization(client, chat_manager):
    """Test ChatManager initialization."""
    assert chat_manager.client == client

def test_ask_simple_query(chat_manager):
    """Test sending a simple query to the chat endpoint."""
    # Mock the client's _make_request method
    chat_manager.client._make_request = MagicMock()
    chat_manager.client._make_request.return_value = {
        "response": "This is a test response",
        "status": "success"
    }
    
    # Send a test query
    response = chat_manager.ask("What is the meaning of life?")
    
    # Verify the request was made correctly
    chat_manager.client._make_request.assert_called_once_with(
        "POST",
        "chat",
        json={"message": "What is the meaning of life?"}
    )
    
    # Verify response
    assert response["response"] == "This is a test response"
    assert response["status"] == "success"

def test_ask_empty_query(chat_manager):
    """Test sending an empty query."""
    # Mock the client's _make_request method
    chat_manager.client._make_request = MagicMock()
    chat_manager.client._make_request.return_value = {
        "response": "Empty query received",
        "status": "success"
    }
    
    # Send an empty query
    response = chat_manager.ask("")
    
    # Verify request was made with empty string
    chat_manager.client._make_request.assert_called_once_with(
        "POST",
        "chat",
        json={"message": ""}
    )
    
    # Verify response
    assert response["response"] == "Empty query received"
    assert response["status"] == "success"

def test_ask_special_characters(chat_manager):
    """Test sending queries with special characters."""
    # Mock the client's _make_request method
    chat_manager.client._make_request = MagicMock()
    
    # Test with various special characters
    special_queries = [
        "Hello\nWorld",  # Newline
        "Question?!@#$%^&*()",  # Special characters
        "Multi\nLine\nQuery",  # Multiple newlines
        "Unicode: 你好",  # Unicode characters
    ]
    
    for query in special_queries:
        chat_manager.ask(query)
        chat_manager.client._make_request.assert_called_with(
            "POST",
            "chat",
            json={"message": query}
        )
        chat_manager.client._make_request.reset_mock()

def test_ask_long_query(chat_manager):
    """Test sending a long query."""
    # Create a long query (1000 characters)
    long_query = "x" * 1000
    
    # Mock the client's _make_request method
    chat_manager.client._make_request = MagicMock()
    chat_manager.client._make_request.return_value = {
        "response": "Response to long query",
        "status": "success"
    }
    
    # Send the long query
    response = chat_manager.ask(long_query)
    
    # Verify request was made correctly
    chat_manager.client._make_request.assert_called_once_with(
        "POST",
        "chat",
        json={"message": long_query}
    )
    
    # Verify response
    assert response["status"] == "success" 