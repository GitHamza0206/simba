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
            
        return self.client.make_request(
            "POST", 
            f"/embed/document", 
            params={"doc_id": document_id, **params}
        )
    
    def get_embedding(self, document_id):
        """
        Get information about an embedding for a document.
        
        Args:
            document_id (str): The ID of the document.
        
        Returns:
            dict: A dictionary containing the embedding information.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client.make_request(
            "GET", 
            f"/embedded_documents", 
            params={"doc_id": document_id}
        )
    
    def list_embeddings(self, limit=100, offset=0):
        """
        List all embeddings.
        
        Args:
            limit (int, optional): Maximum number of embeddings to return. Default is 100.
            offset (int, optional): Offset for pagination. Default is 0.
        
        Returns:
            dict: A dictionary containing a list of embeddings.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        return self.client.make_request(
            "GET", 
            "/embedded_documents", 
            params=params
        )
    
    def embed_documents(self, document_ids, model=None):
        """
        Create embeddings for multiple documents.
        
        Args:
            document_ids (list): List of document IDs to embed.
            model (str, optional): The embedding model to use. If not provided,
                                  the default model will be used.
        
        Returns:
            dict: A dictionary containing the task ID for tracking progress.
        
        Raises:
            Exception: If the API request fails.
        """
        data = {
            "document_ids": document_ids
        }
        
        if model:
            data["model"] = model
            
        return self.client.make_request(
            "POST", 
            "/embed/documents", 
            json=data
        )
    
    def embed_all_documents(self, model=None):
        """
        Create embeddings for all documents.
        
        Args:
            model (str, optional): The embedding model to use. If not provided,
                                  the default model will be used.
        
        Returns:
            dict: A dictionary containing the task ID for tracking progress.
        
        Raises:
            Exception: If the API request fails.
        """
        data = {}
        
        if model:
            data["model"] = model
            
        return self.client.make_request(
            "POST", 
            "/embed/documents", 
            json=data
        )
    
    def delete_embedding(self, document_id):
        """
        Delete an embedding for a document.
        
        Args:
            document_id (str): The ID of the document.
        
        Returns:
            dict: A dictionary confirming deletion.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client.make_request(
            "DELETE", 
            f"/embed/document", 
            params={"doc_id": document_id}
        )
    
    def delete_all_embeddings(self):
        """
        Delete all embeddings.
        
        Returns:
            dict: A dictionary containing the number of embeddings deleted.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client.make_request(
            "DELETE", 
            "/embed/clear_store"
        )
    
    def get_embedding_status(self, task_id):
        """
        Get the status of an embedding task.
        
        Args:
            task_id (str): The ID of the task.
        
        Returns:
            dict: A dictionary containing task status information.
        
        Raises:
            Exception: If the API request fails.
        """
        return self.client.make_request(
            "GET", 
            f"/embed/task/{task_id}"
        )
    
    def get_similarity_search(self, document_id, query, limit=5):
        """
        Perform a similarity search using a document's embedding.
        
        Args:
            document_id (str): The ID of the document to search within.
            query (str): The search query.
            limit (int, optional): Maximum number of results to return. Default is 5.
        
        Returns:
            dict: A dictionary containing search results with scores and content.
        
        Raises:
            Exception: If the API request fails.
        """
        params = {
            "query": query,
            "limit": limit,
            "doc_id": document_id
        }
        
        return self.client.make_request(
            "GET", 
            f"/embed/search", 
            params=params
        ) 