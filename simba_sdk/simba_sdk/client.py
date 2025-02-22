import requests
from typing import Optional, Dict, Any

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

    def ask(self, query: str) -> Dict[str, Any]:
        """
        Send a query to the Simba chat endpoint.
        
        This method sends a POST request to <api_url>/chat with the query message.
        
        Args:
            query (str): The query to send to Simba.
        
        Returns:
            Dict[str, Any]: The JSON response from the server.
        """
        payload = {"message": query}
        response = requests.post(
            f"{self.api_url}/chat",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.text

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a document to Simba for ingestion.
        
        This method sends a POST request to <api_url>/ingestion by uploading the file.
        
        Args:
            file_path (str): The filesystem path to the document.
        
        Returns:
            Dict[str, Any]: The JSON response from the server.
        """
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.api_url}/ingestion",
                files=files,
                headers=self.headers
            )
        response.raise_for_status()
        return response.json()

    # Additional methods (for parsing, retrieval, etc.) can be added here.
    def as_retriever(self):
        response = requests.get(
            f"{self.api_url}/retriever/as_retriever",
            headers=self.headers
        )
        response.raise_for_status()
        return response

