import json
import requests
import time
from typing import Dict, Any, List, Optional, Union


class ParserManager:
    """
    A class that provides parsing functionality for the Simba SDK.
    Enables extracting structured data from documents in various formats.
    """

    def __init__(self, client):
        """
        Initialize the ParserManager with a SimbaClient instance.
        
        Args:
            client: An instance of SimbaClient
        """
        self.client = client
        
    @property
    def headers(self):
        """Get the headers from the client."""
        return self.client.headers
    
    def get_parsers(self) -> Dict[str, Any]:
        """
        Get the list of available parsers.
        
        Returns:
            Dict[str, Any]: List of available parsers
        """
        return self.client._make_request("GET", "parsers")
    
    def parse_document(self, document_id: str, parser: str = "docling", 
                      sync: bool = True,
                      wait_for_completion: bool = False,
                      polling_interval: int = 2,
                      timeout: int = 60) -> Dict[str, Any]:
        """
        Parse a document using the specified parser.

        Args:
            document_id: The ID of the document to parse.
            parser: The parser to use. Default is "docling".
            sync: Whether to parse synchronously. Default is True.
            wait_for_completion: Whether to wait for the parsing task to complete. Default is False.
            polling_interval: How often to check the task status (in seconds). Default is 2.
            timeout: Maximum time to wait for completion (in seconds). Default is 60.

        Returns:
            The parsing result or task information.
        """
        # If sync is True, use the synchronous endpoint
        if sync:
            url = f"{self.client.api_url}/parse/sync"
            # Send document_id as a query parameter instead of in the request body
            params = {"document_id": document_id}
            
            response = requests.post(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
        
        # Otherwise, use the original async endpoint
        url = f"{self.client.api_url}/parse"
        
        payload = {
            "document_id": document_id,
            "parser": parser,
            "sync": False  # Explicitly set to false for async
        }
            
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        result = response.json()
        
        # If we don't need to wait, return the task info immediately
        if not wait_for_completion:
            return result
        
        # Wait for the task to complete
        task_id = result.get("task_id")
        status_url = result.get("status_url")
        
        if not task_id or not status_url:
            return result
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            task_status = self.get_task_status(task_id)
            status = task_status.get("status")
            
            if status == "SUCCESS":
                return task_status
            elif status in ["FAILURE", "REVOKED"]:
                raise Exception(f"Parsing task failed: {task_status}")
            
            time.sleep(polling_interval)
        
        raise TimeoutError(f"Parsing task did not complete within {timeout} seconds")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a parsing task.
        
        Args:
            task_id (str): The ID of the parsing task
            
        Returns:
            Dict[str, Any]: Status information about the task
        """
        url = f"{self.client.api_url}/parsing/tasks/{task_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """
        Get information about all parsing tasks.
        
        Returns:
            Dict[str, Any]: Information about all parsing tasks
        """
        url = f"{self.client.api_url}/parsing/tasks"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # Convenience methods that build on the core parsing functionality
    
    def extract_tables(self, document_id: str, 
                       sync: bool = True) -> Dict[str, Any]:
        """
        Extract tables from a document.

        Args:
            document_id: The ID of the document to extract tables from.
            sync: Whether to extract synchronously. Default is True.

        Returns:
            A dictionary containing the extracted tables.
        """
        if sync:
            # For synchronous processing, use the synchronous endpoint with document_id as query parameter
            url = f"{self.client.api_url}/parse/sync"
            params = {
                "document_id": document_id,
                "feature": "tables"  # Indicate we're extracting tables
            }
            
            response = requests.post(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
        
        # For async processing, use the original endpoint with JSON payload
        url = f"{self.client.api_url}/parse"
        payload = {
            "document_id": document_id,
            "parser": "docling",
            "sync": False,
            "feature": "tables"
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        result = response.json()
        
        # Return the result directly
        return result

    def extract_entities(self, document_id: str, 
                         sync: bool = True) -> Dict[str, Any]:
        """
        Extract entities from a document.

        Args:
            document_id: The ID of the document to extract entities from.
            sync: Whether to extract synchronously. Default is True.

        Returns:
            A dictionary containing the extracted entities.
        """
        if sync:
            # For synchronous processing, use the synchronous endpoint with document_id as query parameter
            url = f"{self.client.api_url}/parse/sync"
            params = {
                "document_id": document_id,
                "feature": "entities"  # Indicate we're extracting entities
            }
            
            response = requests.post(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        # For async processing, use the original endpoint with JSON payload
        url = f"{self.client.api_url}/parse"
        payload = {
            "document_id": document_id,
            "parser": "docling",
            "sync": False,
            "feature": "entities"
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        result = response.json()
        
        # Return the result directly
        return result

    def extract_forms(self, document_id: str, 
                     form_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract form fields from a document.

        Args:
            document_id: The ID of the document to extract form fields from.
            form_type: Optional type of form to extract. Default is None.

        Returns:
            A dictionary containing the extracted form fields.
        """
        # Always use synchronous endpoint for forms extraction by default
        url = f"{self.client.api_url}/parse/sync"
        
        # Use query parameters for the synchronous endpoint
        params = {
            "document_id": document_id,
            "feature": "forms"
        }
        
        if form_type:
            params["form_type"] = form_type
            
        response = requests.post(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        return response.json()

    def extract_text(self, document_id: str, 
                    structured: bool = True,
                    include_layout: bool = False) -> Dict[str, Any]:
        """
        Extract text content from a document.

        Args:
            document_id: The ID of the document to extract text from.
            structured: Whether to extract structured text. Default is True.
            include_layout: Whether to include layout information. Default is False.

        Returns:
            A dictionary containing the extracted text.
        """
        # Always use synchronous endpoint for text extraction by default
        url = f"{self.client.api_url}/parse/sync"
        
        # Use query parameters for the synchronous endpoint
        params = {
            "document_id": document_id,
            "feature": "text",
            "structured": str(structured).lower(),
            "include_layout": str(include_layout).lower()
        }
            
        response = requests.post(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        return response.json()

    def parse_query(self, document_id: str, query: str) -> Dict[str, Any]:
        """
        Extract information from a document based on a natural language query.

        Args:
            document_id: The ID of the document to query.
            query: The natural language query to answer.

        Returns:
            A dictionary containing the query result.
        """
        # Always use synchronous endpoint for query parsing by default
        url = f"{self.client.api_url}/parse/sync"
        
        # Use query parameters for the synchronous endpoint
        params = {
            "document_id": document_id,
            "feature": "query",
            "query": query
        }
            
        response = requests.post(url, params=params, headers=self.headers)
        response.raise_for_status()
        result = response.json()
        
        # Add the query to the result for convenience
        result["query"] = query
        
        return result 