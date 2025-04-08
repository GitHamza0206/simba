import logging
from typing import Dict, List, Optional, Union, cast

from langchain.schema import Document

from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.embeddings.utils import _clean_documents
from simba.models.simbadoc import SimbaDoc
from simba.splitting.splitter import Splitter
logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for handling all embedding operations, including:
    - Adding documents to the vector store
    - Retrieving embedded documents
    - Deleting documents from the vector store
    """

    def __init__(self):
        """Initialize the EmbeddingService with necessary components."""
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.database = get_database()
        self.splitter = Splitter(chunk_size=5000, chunk_overlap=300)  

    def embed_all_documents(self) -> List[Document]:
        """
        Embed all documents in the database into the vector store.

        Returns:
            List of embedded langchain documents
        """
        try:
            # Get all documents from the database
            all_documents = self.database.get_all_documents()
            simba_documents = [cast(SimbaDoc, doc) for doc in all_documents]

            # Convert to Langchain documents
            langchain_documents = [
                doc for simbadoc in simba_documents for doc in simbadoc.documents
            ]

            # Clean documents
            langchain_documents = _clean_documents(langchain_documents)

            # Add documents to vector store
            self.vector_store.add_documents(langchain_documents)

            # Update enabled status for each document
            for doc in simba_documents:
                doc.metadata.enabled = True
                self.database.update_document(doc.id, doc)

            return langchain_documents
        except Exception as e:
            logger.error(f"Error embedding all documents: {str(e)}")
            raise

    def embed_document(self, doc_id: str) -> List[Document]:
        """
        Embed a specific document into the vector store.

        Args:
            doc_id: The ID of the document to embed

        Returns:
            List of embedded langchain documents
        """
        try:
            # Get document from database
            simbadoc: SimbaDoc = self.database.get_document(doc_id)
            if not simbadoc:
                raise ValueError(f"Document {doc_id} not found")

            langchain_documents = simbadoc.documents

            langchain_documents = self.splitter.split_document(langchain_documents) 

            # Clean documents
            langchain_documents = _clean_documents(langchain_documents)

            try:
                # Add documents to vector store
                self.vector_store.add_documents(document_id=doc_id, documents=langchain_documents)

                # Update document status
                simbadoc.metadata.enabled = True
                self.database.update_document(doc_id, simbadoc)

            except ValueError as ve:
                # If the error is about existing IDs, consider it a success
                if "Tried to add ids that already exist" in str(ve):
                    return langchain_documents
                raise ve  # Re-raise if it's a different ValueError

            return langchain_documents

        except Exception as e:
            logger.error(f"Error embedding document {doc_id}: {str(e)}")
            raise

    def get_embedded_documents(self) -> List[Document]:
        """
        Get all documents from the vector store.

        Returns:
            List of embedded documents
        """
        try:
            return self.vector_store.get_documents()
        except Exception as e:
            logger.error(f"Error getting embedded documents: {str(e)}")
            raise

    def delete_document_chunks(self, chunk_ids: List[str]) -> Dict[str, str]:
        """
        Delete specific document chunks from the vector store.

        Args:
            chunk_ids: List of chunk IDs to delete

        Returns:
            Dictionary with status message
        """
        try:
            self.vector_store.delete_documents(chunk_ids)
            return {"message": f"Deleted {len(chunk_ids)} document chunks"}
        except Exception as e:
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise

    def delete_document(self, doc_id: str) -> Dict[str, str]:
        """
        Delete all chunks of a document from the vector store.

        Args:
            doc_id: Document ID to delete

        Returns:
            Dictionary with status message
        """
        try:
            simbadoc: SimbaDoc = self.database.get_document(doc_id)
            if not simbadoc:
                raise ValueError(f"Document {doc_id} not found")

            #docs_ids: List[str] = [doc.id for doc in simbadoc.documents]
            self.vector_store.delete_documents(doc_id)

            # Update document status
            simbadoc.metadata.enabled = False
            self.database.update_document(doc_id, simbadoc)

            return {"message": f"Document {doc_id} deleted from vector store"}
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            raise

    def clear_store(self) -> Dict[str, str]:
        """
        Clear the entire vector store.

        Returns:
            Dictionary with status message
        """
        try:
            self.vector_store.clear_store()
            return {"message": "Vector store cleared"}
        except Exception as e:
            logger.error(f"Error clearing vector store: {str(e)}")
            raise
