"""
Abstract base class for database services in Simba.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Union

from simba.models.simbadoc import SimbaDoc


class DatabaseService(ABC):
    """
    Abstract base class defining the interface for document storage services.
    
    All database implementations must inherit from this class and implement
    its methods to provide a consistent API for document storage.
    """
    
    @abstractmethod
    def insert_document(self, document: SimbaDoc) -> str:
        """
        Insert a document into the database.
        
        Args:
            document: The document to insert
            
        Returns:
            The ID of the inserted document
        """
        pass
    
    @abstractmethod
    def insert_documents(self, documents: List[SimbaDoc]) -> List[str]:
        """
        Insert multiple documents into the database.
        
        Args:
            documents: The documents to insert
            
        Returns:
            List of document IDs that were inserted
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[SimbaDoc]:
        """
        Retrieve a document by its ID.
        
        Args:
            document_id: The ID of the document to retrieve
            
        Returns:
            The document, or None if not found
        """
        pass
    
    @abstractmethod
    def get_all_documents(self) -> List[SimbaDoc]:
        """
        Retrieve all documents from the database.
        
        Returns:
            List of all documents
        """
        pass
    
    @abstractmethod
    def update_document(self, document_id: str, document: SimbaDoc) -> bool:
        """
        Update a document in the database.
        
        Args:
            document_id: The ID of the document to update
            document: The new document data
            
        Returns:
            True if the document was updated, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the database.
        
        Args:
            document_id: The ID of the document to delete
            
        Returns:
            True if the document was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete multiple documents from the database.
        
        Args:
            document_ids: The IDs of the documents to delete
            
        Returns:
            True if all documents were deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def clear_database(self) -> bool:
        """
        Clear all documents from the database.
        
        Returns:
            True if the database was cleared, False otherwise
        """
        pass
    
    @abstractmethod
    def query_documents(self, filters: Dict[str, Any]) -> List[SimbaDoc]:
        """
        Query documents from the database using filters.
        
        Args:
            filters: Dictionary of field-value pairs to filter by
            
        Returns:
            List of matching documents
        """
        pass
    
    
    
    @abstractmethod
    def health_check(self) -> Dict[str, Union[bool, str]]:
        """
        Check the health of the database connection.
        
        Returns:
            Dictionary with health status information
        """
        pass 