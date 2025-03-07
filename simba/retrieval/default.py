"""
Default vector similarity retriever implementation.
"""

from typing import List, Optional

from langchain.schema import Document

from simba.retrieval.base import BaseRetriever
from simba.vector_store import VectorStoreService


class DefaultRetriever(BaseRetriever):
    """Default vector similarity search retriever."""

    def __init__(self, vector_store: Optional[VectorStoreService] = None, k: int = 5, **kwargs):
        """
        Initialize the default retriever.

        Args:
            vector_store: Optional vector store to use
            k: Default number of documents to retrieve
            **kwargs: Additional parameters
        """
        super().__init__(vector_store)
        self.default_k = k

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieve documents using default similarity search.

        Args:
            query: The query string
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve (overrides instance default)
                - score_threshold: Minimum score threshold for results
                - filter: Filter criteria

        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", self.default_k)
        score_threshold = kwargs.get("score_threshold", None)
        filter_dict = kwargs.get("filter", None)

        # Create search kwargs dictionary with all parameters
        search_kwargs = {"k": k}

        # Only add these if they are not None
        if score_threshold is not None:
            search_kwargs["score_threshold"] = score_threshold

        if filter_dict is not None:
            search_kwargs["filter"] = filter_dict

        return self.store.as_retriever(
            search_type="similarity", search_kwargs=search_kwargs
        ).get_relevant_documents(query)
