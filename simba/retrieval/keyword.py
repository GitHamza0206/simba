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

    def __init__(self, vector_store: Optional[VectorStoreService] = None, **kwargs):
        """
        Initialize the keyword retriever.

        Args:
            vector_store: Optional vector store service
            **kwargs: Additional parameters for BM25
        """
        super().__init__(vector_store)
        # Get all documents from the vector store
        all_documents = self.store.get_documents()
        # Initialize BM25 retriever with these documents
        self.bm25_retriever = BM25Retriever.from_documents(all_documents, **kwargs)

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieve documents using BM25 keyword search.

        Args:
            query: The query string
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve (default: 5)

        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", 5)
        return self.bm25_retriever.get_relevant_documents(query)[:k]
