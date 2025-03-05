import requests
from typing import Optional, Dict, Any, Union
from .document import DocumentManager
from .chat import ChatManager
from .parser import ParserManager
from .embed import EmbeddingManager
from .retrieve import RetrieveManager

class SimbaClient:
    """
    A high-level client for interacting with the Simba Core API.
    """

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        Initialize the client with the Simba API URL and optional API key.
        
        Args:
            api_url (str): The base URL of the Simba Core API.
            api_key (Optional[str]): Optional API key for authorization.
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            
        # Initialize managers
        self.documents = DocumentManager(self)
        self.chat = ChatManager(self)
        self.parser = ParserManager(self)
        self.embedding = EmbeddingManager(self)
        self.retriever = RetrieveManager(self)

    def _make_request(self, method: str, endpoint: str, 
                     params: Optional[Dict] = None, 
                     json: Optional[Dict] = None, 
                     data: Optional[Dict] = None,
                     files: Optional[Dict] = None,
                     stream: bool = False) -> Union[Dict, str, bytes]:
        """
        Helper method to make API requests.
        
        Args:
            method: HTTP method to use (GET, POST, etc.)
            endpoint: API endpoint (will be appended to base URL)
            params: Query parameters
            json: JSON body data
            data: Form data
            files: Files to upload
            stream: Whether to stream the response
            
        Returns:
            Response data (parsed JSON, text, or bytes depending on context)
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        # Handle files upload - don't send Content-Type header
        request_headers = self.headers
        if files:
            request_headers = {k: v for k, v in self.headers.items() 
                              if k != 'Content-Type'}
        
        response = requests.request(
            method,
            url,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
            stream=stream
        )
        response.raise_for_status()
        
        if stream:
            return response.content
        
        try:
            return response.json()
        except ValueError:
            return response.text

    
