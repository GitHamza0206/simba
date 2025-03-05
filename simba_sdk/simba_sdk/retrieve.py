import requests
from typing import Dict, Any, List, Optional, Union


class RetrieveManager:
    """
    A class that provides retrieval functionality for the Simba SDK.
    Enables retrieving relevant content from documents using different strategies.
    """

    def __init__(self, client):
        """
        Initialize the RetrieveManager with a SimbaClient instance.
        
        Args:
            client: An instance of SimbaClient
        """
        self.client = client
        
    @property
    def headers(self):
        """Get the headers from the client."""
        return self.client.headers
    
    def get_retrieval_strategies(self) -> Dict[str, Any]:
        """
        Get the list of available retrieval strategies.
        
        Returns:
            Dict[str, Any]: List of available retrieval strategies
        """
        url = f"{self.client.api_url}/retriever/as_retriever"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def retrieve(self, 
                query: str, 
                method: str = "semantic", 
                filter: Optional[Dict[str, Any]] = None,
                k: int = 5,
                score_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Retrieve relevant content based on a query using the specified strategy.

        Args:
            query: The search query.
            strategy: The retrieval strategy to use. Default is "semantic".
                     Options may include: "semantic", "keyword", "hybrid", etc.
            filters: Optional filters to narrow down the search scope.
            top_k: Maximum number of results to return. Default is 5.
            collection_id: Optional collection ID to search within a specific collection.
            document_ids: Optional list of document IDs to restrict the search.
            include_metadata: Whether to include metadata in the results. Default is True.
            similarity_threshold: Optional threshold for similarity scores.

        Returns:
            Dict[str, Any]: Retrieved results and related information.
        """
        url = f"{self.client.api_url}/retriever/retrieve"
        
        payload = {
            "query": query,
            "method": method,
            "k": k
        }
        
        if filter:
            payload["filter"] = filter
            
        if score_threshold is not None:
            payload["score_threshold"] = score_threshold
            
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    