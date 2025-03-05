import pytest
import responses
import json
from unittest.mock import MagicMock, patch
from simba_sdk import SimbaClient, RetrieveManager


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
    