import os
import json
from typing import Dict, Any, List, Optional, Union, BinaryIO
import requests
from pathlib import Path


class DocumentManager:
    """
    A class that provides document management functionality for Simba.
    Handles CRUD operations for documents in the knowledge base.
    """

    def __init__(self, client):
        """
        Initialize the DocumentManager with a SimbaClient instance.
        
        Args:
            client: An instance of SimbaClient
        """
        self.client = client
        self.base_url = f"{client.api_url}/ingestion"
        self.headers = client.headers

    def create(self, file_path: Union[str, Path], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload and ingest a document to Simba knowledge base.
        
        Args:
            file_path (Union[str, Path]): Path to the file to be ingested
            metadata (Optional[Dict[str, Any]]): Additional metadata about the document
            
        Returns:
            Dict[str, Any]: Response data with document ID and status
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'rb') as file:
            return self.create_from_file(file, file_path.name, metadata)
    
    def create_from_file(self, file: BinaryIO, filename: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload and ingest a file object to Simba knowledge base.
        
        Args:
            file (BinaryIO): File-like object to be ingested
            filename (str): Name of the file
            metadata (Optional[Dict[str, Any]]): Additional metadata about the document
            
        Returns:
            Dict[str, Any]: Response data with document ID and status
        """
        files = {'files': (filename, file)}
        data = {}
        
        if metadata and 'folder_path' in metadata:
            data['folder_path'] = metadata.pop('folder_path')
            
        if metadata:
            data['metadata'] = json.dumps(metadata)
            
        response = requests.post(
            self.base_url,
            files=files,
            data=data,
            headers={k: v for k, v in self.headers.items() 
                     if k != 'Content-Type'}
        )
        response.raise_for_status()
        return response.json()
    
    def create_from_text(self, text: str, name: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a document from raw text.
        
        Args:
            text (str): Content of the document
            name (str): Name for the document
            metadata (Optional[Dict[str, Any]]): Additional metadata about the document
            
        Returns:
            Dict[str, Any]: Response data with document ID and status
        """
        temp_file_path = Path(f"{name}.txt")
        try:
            with open(temp_file_path, 'w') as f:
                f.write(text)
            
            with open(temp_file_path, 'rb') as f:
                return self.create_from_file(f, f"{name}.txt", metadata)
        finally:
            if temp_file_path.exists():
                os.unlink(temp_file_path)
    
    def get(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve a document by its ID.
        
        Args:
            document_id (str): The ID of the document to retrieve
            
        Returns:
            Dict[str, Any]: Document data including metadata and chunks
        """
        response = requests.get(
            f"{self.base_url}/{document_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def list(self, page: int = 1, 
             page_size: int = 20, 
             filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List documents in the knowledge base.
        
        Args:
            page (int): Page number for pagination
            page_size (int): Number of documents per page
            filters (Optional[Dict[str, Any]]): Metadata filters to apply
            
        Returns:
            Dict[str, Any]: Paginated list of documents
        """
        response = requests.get(
            self.base_url,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update(self, document_id: str, 
               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a document's metadata.
        
        Args:
            document_id (str): The ID of the document to update
            metadata (Optional[Dict[str, Any]]): New metadata to apply
            
        Returns:
            Dict[str, Any]: Updated document data
        """
        current_doc = self.get(document_id)
        
        if metadata:
            if 'metadata' in current_doc:
                current_doc['metadata'].update(metadata)
            else:
                current_doc['metadata'] = metadata
            
        response = requests.put(
            f"{self.base_url}/update_document",
            params={"doc_id": document_id},
            json=current_doc,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id (str): The ID of the document to delete
            
        Returns:
            Dict[str, Any]: Response indicating success or failure
        """
        response = requests.delete(
            self.base_url,
            params={"uids": [document_id]},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def preview(self, document_id: str) -> bytes:
        """
        Get a preview of the document.
        
        Args:
            document_id (str): The ID of the document to preview
            
        Returns:
            bytes: Binary content of the document for preview
        """
        response = requests.get(
            f"{self.client.api_url}/preview/{document_id}",
            headers=self.headers,
            stream=True
        )
        response.raise_for_status()
        return response.content

    def clear_db(self) -> Dict[str, Any]:
        """
        Clear all documents from the database.
        
        WARNING: This will permanently delete all documents in the system.
        This is a destructive operation and cannot be undone.
        
        Returns:
            Dict[str, Any]: A response confirming the database was cleared
        
        Raises:
            Exception: If the operation fails
        """
        return self.client._make_request(
            "DELETE",
            "/db/clear"
        ) 