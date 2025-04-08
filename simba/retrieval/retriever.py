"""
Main retriever interface for document retrieval.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from langchain.schema import Document

from simba.core.config import settings
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.retrieval.base import BaseRetriever, RetrievalMethod
from simba.retrieval.factory import RetrieverFactory
from simba.auth.auth_service import get_supabase_client
logger = logging.getLogger(__name__)


class Retriever:
    """
    Main retrieval interface for the application.
    This class serves as a facade over the various retrieval strategies.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the retriever with a vector store and configuration.

        Args:
            config: Optional configuration dictionary. If not provided,
                  will be loaded from application settings.
        """
        self.store = VectorStoreFactory.get_vector_store()
        self.factory = RetrieverFactory

        # Get default retriever from configuration
        self.default_retriever = self.factory.from_config(config)
        logger.info(
            f"Initialized retriever with default strategy: {type(self.default_retriever).__name__}"
        )

    def retrieve(
        self, query: str, method: Union[str, RetrievalMethod] = None, **kwargs
    ) -> List[Document]:
        """
        Retrieve documents using the specified method.

        Args:
            query: The query string
            method: Retrieval method to use. If None, uses the configured default.
            user_id: User ID for multi-tenant filtering (required for security)
            **kwargs: Additional parameters for the retrieval method

        Returns:
            List of relevant documents
        """
        supabase = get_supabase_client()    
        user = supabase.auth.get_user()
        user_id = user.user.id

        # If method is specified, create a retriever for it
        if method:
            retriever = self.factory.get_retriever(method, vector_store=self.store)
            logger.debug(f"Using retrieval strategy '{method}' for query: {query[:50]}...")
        else:
            # Use the default retriever
            retriever = self.default_retriever
            logger.debug(f"Using default retrieval strategy for query: {query[:50]}...")

        # Log warning if user_id is not provided (insecure)
        if user_id is None:
            logger.warning("retrieve() called without user_id - this is not secure for multi-tenant systems")

        # Add user_id to the kwargs for multi-tenancy
        if user_id:
            kwargs["user_id"] = user_id

        # Retrieve documents
        docs = retriever.retrieve(query, **kwargs)
        logger.debug(f"Retrieved {len(docs)} documents using {type(retriever).__name__}")
        return docs

    def as_retriever(self, method: Union[str, RetrievalMethod] = None, **kwargs):
        """
        Return a LangChain-compatible retriever.

        Args:
            method: Retrieval method to use. If None, uses the configured default.
            **kwargs: Additional parameters for the retriever

        Returns:
            A LangChain retriever
        """
        # If method is specified, create a retriever for it
        if method:
            retriever = self.factory.get_retriever(method, vector_store=self.store)
            logger.debug(f"Creating LangChain retriever with strategy: {method}")
        else:
            # Use the default retriever
            retriever = self.default_retriever
            logger.debug(
                f"Creating LangChain retriever with default strategy: {type(retriever).__name__}"
            )

        # Return as a LangChain retriever
        return retriever.as_retriever(**kwargs)

    def as_ensemble_retriever(
        self,
        retrievers: Optional[List[BaseRetriever]] = None,
        weights: Optional[List[float]] = None,
        **kwargs,
    ):
        """
        Create an ensemble retriever that combines multiple strategies.

        Args:
            retrievers: List of retrievers to ensemble
            weights: Weights for each retriever
            **kwargs: Additional parameters for the ensemble

        Returns:
            An ensemble retriever
        """
        # Import here to avoid circular import
        from simba.retrieval.ensemble import EnsembleSearchRetriever

        # Create an ensemble retriever
        ensemble = EnsembleSearchRetriever(
            vector_store=self.store, retrievers=retrievers, weights=weights
        )

        logger.debug(f"Created ensemble retriever with {len(ensemble.retrievers)} strategies")

        # Return as a LangChain retriever
        return ensemble.as_retriever(**kwargs)


def run_example():
    """Example usage of the retriever."""
    # Create a retriever with default config
    retriever = Retriever()

    # Example query
    query = "How does vector search work?"

    print(f"Query: {query}")
    print(f"Default retriever type: {type(retriever.default_retriever).__name__}")

    # Retrieve using default configured retriever
    print("\nUsing default configured retriever:")
    docs = retriever.retrieve(query, k=3)
    print(f"Found {len(docs)} documents")

    # Try different retrieval methods
    for method in [
        RetrievalMethod.DEFAULT,
        RetrievalMethod.SEMANTIC,
        RetrievalMethod.KEYWORD,
        RetrievalMethod.HYBRID,
        RetrievalMethod.ENSEMBLE,
    ]:
        print(f"\nRetrieval method: {method}")
        try:
            docs = retriever.retrieve(query, method=method, k=3)
            print(f"Found {len(docs)} documents")
            for i, doc in enumerate(docs):
                print(f"Document {i+1}: {doc.page_content[:100]}...")
        except Exception as e:
            print(f"Error with {method} retrieval: {str(e)}")

    print("\nDone!")


if __name__ == "__main__":
    run_example()
