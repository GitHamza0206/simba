"""
Embedding Manager for the Simba Client.

This module provides functionality for creating and managing document embeddings
for semantic search and similarity analysis.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path


class EmbeddingManager:
    """
    Manager for document embedding operations.
    
    This class provides methods for creating, retrieving, and managing
    document embeddings for semantic search and similarity analysis.
    """
    
    def __init__(self, client):
        """
        Initialize the EmbeddingManager.
        
        Args:
            client (SimbaClient): The Simba client instance to use for API requests.
        """
        self.client = client
    
    def embed_document(self, document_id, model=None):
        """
        Create an embedding for a document.
        
        Args:
            document_id (str): The ID of the document to embed.
            model (str, optional): The embedding model to use. If not provided,
                                  the default model will be used.
        
        Returns:
            dict: A dictionary containing the embedding information.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {}
        if model:
            params["model"] = model
            
        return self.client._make_request(
            "POST", 
            f"/embed/document", 
            params=params
        )
    
    def get_embedding(self, document_id):
        """
        Get embedding information for a document.
        
        Args:
            document_id (str): The ID of the document to get the embedding for.
        
        Returns:
            dict: A dictionary containing the embedding information.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client._make_request(
            "GET", 
            f"/embed/document/{document_id}"
        )
    
    def list_embeddings(self, limit=100, offset=0):
        """
        List all embeddings.
        
        Args:
            limit (int, optional): The maximum number of embeddings to return.
                                  Defaults to 100.
            offset (int, optional): The offset to start from when returning 
                                   embeddings. Defaults to 0.
        
        Returns:
            dict: A dictionary containing the list of embeddings.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        return self.client._make_request(
            "GET", 
            "/embedded_documents", 
            params=params
        )
    
    def embed_documents(self, document_ids, model=None):
        """
        Create embeddings for multiple documents.
        
        Args:
            document_ids (list): A list of document IDs to embed.
            model (str, optional): The embedding model to use. If not provided,
                                  the default model will be used.
        
        Returns:
            dict: A dictionary containing the embedding information.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {
            "doc_ids": document_ids
        }
        
        if model:
            params["model"] = model
            
        return self.client._make_request(
            "POST", 
            "/embed/documents", 
            json=params
        )
    
    def embed_all_documents(self, model=None):
        """
        Create embeddings for all documents.
        
        Args:
            model (str, optional): The embedding model to use. If not provided,
                                  the default model will be used.
        
        Returns:
            dict: A dictionary containing the embedding information.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {}
        
        if model:
            params["model"] = model
            
        return self.client._make_request(
            "POST", 
            "/embed/all", 
            json=params
        )
    
    def delete_embedding(self, document_id):
        """
        Delete an embedding for a document.
        
        Args:
            document_id (str): The ID of the document to delete the embedding for.
        
        Returns:
            dict: A dictionary confirming the embedding was deleted.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client._make_request(
            "DELETE", 
            f"/embed/document", 
            params={"doc_id": document_id}
        )
    
    def delete_all_embeddings(self):
        """
        Delete all embeddings.
        
        Returns:
            dict: A dictionary confirming all embeddings were deleted.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client._make_request(
            "DELETE", 
            "/embed/clear_store"
        )
    
    def clear_store(self):
        """
        Clear the vector store containing all embeddings.
        
        This is an alias for delete_all_embeddings() that provides a more explicit name
        for the operation of completely clearing the vector store.
        
        Returns:
            dict: A dictionary confirming the store was cleared.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client._make_request(
            "DELETE", 
            "/embed/clear_store"
        )
    
    def get_embedding_status(self, task_id):
        """
        Get the status of an embedding task.
        
        Args:
            task_id (str): The ID of the task to get the status for.
        
        Returns:
            dict: A dictionary containing the task status.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client._make_request(
            "GET", 
            f"/task/{task_id}/status"
        )
    
    def get_similarity_search(self, document_id, query, limit=5):
        """
        Perform a similarity search for a document.
        
        Args:
            document_id (str): The ID of the document to search against.
            query (str): The query text to search for.
            limit (int, optional): The maximum number of results to return.
                                  Defaults to 5.
        
        Returns:
            dict: A dictionary containing the search results.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {
            "query": query,
            "limit": limit,
            "doc_id": document_id
        }
        
        return self.client._make_request(
            "GET", 
            "/embed/search", 
            params=params
        ) 