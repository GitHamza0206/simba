"""
Unit tests for the EmbeddingManager class.
"""

import unittest
from unittest.mock import MagicMock, patch
import pytest

from simba_sdk import EmbeddingManager, SimbaClient

class TestEmbeddingManager(unittest.TestCase):
    """Test cases for the EmbeddingManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = MagicMock()
        self.client._make_request = MagicMock()
        self.manager = EmbeddingManager(self.client)
    
    def test_init(self):
        """Test the initialization of the EmbeddingManager."""
        self.assertEqual(self.manager.client, self.client)
    
    def test_embed_document(self):
        """Test embedding a single document."""
        # Setup mock response
        expected_response = {"embedding_id": "emb123", "status": "success"}
        self.client._make_request.return_value = expected_response
        
        # Test without model parameter
        response = self.manager.embed_document("doc123")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "POST", 
            "/embed/document", 
            params={}
        )
        
        # Test with model parameter
        response = self.manager.embed_document("doc123", model="text-embedding-ada-002")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "POST", 
            "/embed/document", 
            params={"model": "text-embedding-ada-002"}
        )
    
    def test_get_embedding(self):
        """Test retrieving embedding information for a document."""
        # Setup mock response
        expected_response = {
            "document_id": "doc123",
            "model": "text-embedding-ada-002",
            "dimensions": 1536,
            "created_at": "2023-01-01T00:00:00Z"
        }
        self.client._make_request.return_value = expected_response
        
        # Test the method
        response = self.manager.get_embedding("doc123")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "GET", 
            "/embed/document/doc123"
        )
    
    def test_list_embeddings(self):
        """Test listing all embeddings."""
        # Setup mock response
        expected_response = {
            "embeddings": [
                {
                    "document_id": "doc123",
                    "model": "text-embedding-ada-002",
                    "dimensions": 1536
                },
                {
                    "document_id": "doc456",
                    "model": "text-embedding-ada-002",
                    "dimensions": 1536
                }
            ],
            "total": 2
        }
        self.client._make_request.return_value = expected_response
        
        # Test with default parameters
        response = self.manager.list_embeddings()
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "GET", 
            "/embedded_documents", 
            params={"limit": 100, "offset": 0}
        )
        
        # Test with custom parameters
        response = self.manager.list_embeddings(limit=10, offset=5)
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "GET", 
            "/embedded_documents", 
            params={"limit": 10, "offset": 5}
        )
    
    def test_embed_documents(self):
        """Test embedding multiple documents."""
        # Setup mock response
        expected_response = {"task_id": "task123", "status": "pending"}
        self.client._make_request.return_value = expected_response
        
        # Test without model parameter
        document_ids = ["doc123", "doc456"]
        response = self.manager.embed_documents(document_ids)
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "POST", 
            "/embed/documents", 
            json={"doc_ids": document_ids}
        )
        
        # Test with model parameter
        response = self.manager.embed_documents(document_ids, model="text-embedding-ada-002")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "POST", 
            "/embed/documents", 
            json={"doc_ids": document_ids, "model": "text-embedding-ada-002"}
        )
    
    def test_embed_all_documents(self):
        """Test embedding all documents."""
        # Setup mock response
        expected_response = {"task_id": "task123", "status": "pending"}
        self.client._make_request.return_value = expected_response
        
        # Test without model parameter
        response = self.manager.embed_all_documents()
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "POST", 
            "/embed/all", 
            json={}
        )
        
        # Test with model parameter
        response = self.manager.embed_all_documents(model="text-embedding-ada-002")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "POST", 
            "/embed/all", 
            json={"model": "text-embedding-ada-002"}
        )
    
    def test_delete_embedding(self):
        """Test deleting an embedding."""
        # Setup mock response
        expected_response = {"status": "success"}
        self.client._make_request.return_value = expected_response
        
        # Test the method
        response = self.manager.delete_embedding("doc123")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "DELETE", 
            "/embed/document", 
            params={"doc_id": "doc123"}
        )
    
    def test_delete_all_embeddings(self):
        """Test deleting all embeddings."""
        # Setup mock response
        expected_response = {"status": "success", "count": 5}
        self.client._make_request.return_value = expected_response
        
        # Test the method
        response = self.manager.delete_all_embeddings()
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "DELETE", 
            "/embed/clear_store"
        )
    
    def test_get_embedding_status(self):
        """Test checking the status of an embedding task."""
        # Setup mock response
        expected_response = {
            "task_id": "task123",
            "state": "SUCCESS",
            "result": {"document_ids": ["doc123", "doc456"]}
        }
        self.client._make_request.return_value = expected_response
        
        # Test the method
        response = self.manager.get_embedding_status("task123")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "GET", 
            "/task/task123/status"
        )
    
    def test_get_similarity_search(self):
        """Test performing a similarity search."""
        # Setup mock response
        expected_response = {
            "results": [
                {"score": 0.95, "content": "Sample text 1"},
                {"score": 0.85, "content": "Sample text 2"}
            ]
        }
        self.client._make_request.return_value = expected_response
        
        # Test with default limit
        response = self.manager.get_similarity_search("doc123", "sample query")
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "GET", 
            "/embed/search", 
            params={"query": "sample query", "limit": 5, "doc_id": "doc123"}
        )
        
        # Test with custom limit
        response = self.manager.get_similarity_search("doc123", "sample query", limit=10)
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "GET", 
            "/embed/search", 
            params={"query": "sample query", "limit": 10, "doc_id": "doc123"}
        )
    
    def test_clear_store(self):
        """Test clearing the vector store."""
        # Setup mock response
        expected_response = {"status": "success", "message": "Store cleared"}
        self.client._make_request.return_value = expected_response
        
        # Test the method
        response = self.manager.clear_store()
        self.assertEqual(response, expected_response)
        self.client._make_request.assert_called_with(
            "DELETE", 
            "/embed/clear_store"
        )

if __name__ == "__main__":
    unittest.main() 