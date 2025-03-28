"""
Keyword-based retriever using BM25.
"""

from typing import List, Optional

from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever

from simba.retrieval.base import BaseRetriever
from simba.vector_store import VectorStoreService


class KeywordRetriever(BaseRetriever):
    """Keyword-based retriever using BM25."""

    def __init__(
        self, vector_store: Optional[VectorStoreService] = None, user_id: str = None, **kwargs
    ):
        """
        Initialize the keyword retriever.

        Args:
            vector_store: Optional vector store service
            user_id: User ID for filtering documents (multi-tenancy)
            **kwargs: Additional parameters for BM25
        """
        super().__init__(vector_store)
        # Get documents from the vector store, filtered by user_id if provided
        all_documents = self.store.get_documents(user_id=user_id)
        # Initialize BM25 retriever with these documents
        self.bm25_retriever = BM25Retriever.from_documents(all_documents, **kwargs)
        # Store user_id for future updates
        self.user_id = user_id

    def retrieve(self, query: str, user_id: str = None, **kwargs) -> List[Document]:
        """
        Retrieve documents using BM25 keyword search.

        Args:
            query: The query string
            user_id: User ID for multi-tenant filtering
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve (default: 5)

        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", 5)

        # If user_id changed or is newly provided, update the documents
        if (user_id and self.user_id != user_id) or (user_id and not self.user_id):
            all_documents = self.store.get_documents(user_id=user_id)
            self.bm25_retriever = BM25Retriever.from_documents(all_documents, **kwargs)
            self.user_id = user_id

        return self.bm25_retriever.get_relevant_documents(query)[:k]
