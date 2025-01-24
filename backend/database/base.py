from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List

class DocumentDatabase(ABC):
    """Abstract base class for document database implementations"""
    
    @abstractmethod
    def insert_document(self, document: Dict[str, Any]) -> str:
        """Insert a new document and return its ID"""
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID"""
        pass
    
    @abstractmethod
    def get_all_documents(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all documents"""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID"""
        pass
    
    @abstractmethod
    def update_document(self, document_id: str, updates: Dict[str, Any]) -> bool:
        """Update a document by ID"""
        pass 