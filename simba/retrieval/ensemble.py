"""
Ensemble retriever that combines multiple strategies.
"""

from typing import List, Optional

from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document

from simba.retrieval.base import BaseRetriever
from simba.vector_store import VectorStoreService


class EnsembleSearchRetriever(BaseRetriever):
    """Ensemble retriever that combines multiple strategies."""

    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        retrievers: Optional[List[BaseRetriever]] = None,
        weights: Optional[List[float]] = None,
    ):
        """
        Initialize the ensemble retriever.

        Args:
            vector_store: Optional vector store service
            retrievers: List of retrievers to ensemble
            weights: Optional weights for each retriever
        """
        super().__init__(vector_store)

        # Import here to avoid circular import
        from simba.retrieval.default import DefaultRetriever
        from simba.retrieval.semantic import SemanticRetriever

        # Create default retrievers if none provided
        if retrievers is None:
            retrievers = [
                DefaultRetriever(self.store),
                SemanticRetriever(self.store),
            ]
            weights = [0.5, 0.5]

        # Ensure weights are provided and sum to 1
        if weights is None:
            weights = [1.0 / len(retrievers)] * len(retrievers)
        elif abs(sum(weights) - 1.0) > 1e-6:
            normalized = [w / sum(weights) for w in weights]
            weights = normalized

        self.retrievers = retrievers
        self.weights = weights

    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieve documents using an ensemble of methods.

        Args:
            query: The query string
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve (default: 5)

        Returns:
            List of relevant documents
        """
        k = kwargs.get("top_k", 5)  

        # Get raw retrievers
        lc_retrievers = [r.as_retriever(search_kwargs={"top_k": k * 2}) for r in self.retrievers]

        # Create LangChain ensemble
        ensemble = EnsembleRetriever(retrievers=lc_retrievers, weights=self.weights)

        return ensemble.get_relevant_documents(query)[:k]
