"""
Abstract base retriever class for document retrieval.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from langchain.schema import Document

from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.vector_store import VectorStoreService


class RetrievalMethod(str, Enum):
    """Enumeration of supported retrieval methods."""

    DEFAULT = "default"
    ENSEMBLE = "ensemble"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    RERANKED = "reranked"


class BaseRetriever(ABC):
    """
    Abstract base class for document retrieval.
    All retrieval strategy implementations should inherit from this class.
    """

    def __init__(self, vector_store: Optional[VectorStoreService] = None):
        """
        Initialize the retriever.

        Args:
            vector_store: Optional vector store service. If not provided,
                          will be initialized from the factory.
        """
        self.store = vector_store or VectorStoreFactory.get_vector_store()

    @abstractmethod
    def retrieve(self, query: str, user_id: str = None, **kwargs) -> List[Document]:
        """
        Retrieve relevant documents for the given query.

        Args:
            query: The search query
            user_id: User ID for multi-tenant filtering
            **kwargs: Additional retrieval parameters

        Returns:
            List of relevant documents
        """
        pass
