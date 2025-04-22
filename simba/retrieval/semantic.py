"""
Semantic retriever with score thresholding.
"""

from typing import Any, Dict, List, Optional

from langchain.schema import Document

from simba.retrieval.base import BaseRetriever
from simba.vector_store import VectorStoreService


class SemanticRetriever(BaseRetriever):
    """Semantic retriever with score thresholding."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        k: int = 5,
        score_threshold: float = 0.5,
        **kwargs
    ):
        """
        Initialize the semantic retriever.

        Args:
            vector_store: Optional vector store to use
            k: Default number of documents to retrieve
            score_threshold: Default minimum similarity score to include
            **kwargs: Additional parameters
        """
        super().__init__(vector_store)
        self.default_k = k
        self.default_score_threshold = score_threshold

    def retrieve(self, query: str, user_id: str = None, **kwargs) -> List[Document]:
        """
        Retrieve documents using semantic search with configurable thresholds.

        Args:
            query: The query string
            user_id: User ID for multi-tenant filtering
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve (overrides instance default)
                - score_threshold: Minimum similarity score (overrides instance default)
                - filter: Metadata filters to apply to the search

        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", self.default_k)
        score_threshold = kwargs.get("score_threshold", self.default_score_threshold)
        filter_dict = kwargs.get("filter", None)
        
        search_kwargs = {"k": k, "score_threshold": score_threshold, "filter": filter_dict}
        
        # Add user_id to search kwargs for multi-tenancy if provided
        if user_id:
            search_kwargs["user_id"] = user_id
        
        return self.store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=search_kwargs,
        ).get_relevant_documents(query)
