"""
Factory for creating retrievers based on method names.
"""

import logging
from typing import Any, Dict, Union

from simba.retrieval.base import BaseRetriever, RetrievalMethod
from simba.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class RetrieverFactory:
    """Factory for creating retrievers based on method names."""

    @staticmethod
    def get_retriever(
        method: Union[str, RetrievalMethod], vector_store=None, **kwargs
    ) -> BaseRetriever:
        """
        Get a retriever instance for the specified method.

        Args:
            method: Retrieval method name or enum
            vector_store: Optional vector store to use
            **kwargs: Additional parameters for the retriever

        Returns:
            A retriever instance
        """
        # Import here to avoid circular imports
        from simba.retrieval.default import DefaultRetriever
        from simba.retrieval.ensemble import EnsembleSearchRetriever
        from simba.retrieval.hybrid import HybridRetriever
        from simba.retrieval.keyword import KeywordRetriever
        from simba.retrieval.semantic import SemanticRetriever

        # Convert string to enum if needed
        if isinstance(method, str):
            try:
                method = RetrievalMethod(method)
                logger.debug(f"Converted string '{method}' to retrieval method enum")
            except ValueError:
                # Default to DEFAULT if string doesn't match any enum
                logger.warning(f"Invalid retrieval method: '{method}', falling back to DEFAULT")
                method = RetrievalMethod.DEFAULT

        # Filter kwargs to only include relevant parameters for each retriever type
        filtered_kwargs = {"vector_store": vector_store} if vector_store else {}

        # Include k parameter for all retrievers if present
        if "k" in kwargs:
            filtered_kwargs["k"] = kwargs.get("k")

        # Create the appropriate retriever with filtered parameters
        if method == RetrievalMethod.SEMANTIC:
            # Add semantic-specific parameters
            if "score_threshold" in kwargs:
                filtered_kwargs["score_threshold"] = kwargs.get("score_threshold")
            if "filter" in kwargs:
                filtered_kwargs["filter"] = kwargs.get("filter")
            logger.debug(f"Creating SemanticRetriever with params: {filtered_kwargs.keys()}")
            return SemanticRetriever(**filtered_kwargs)

        elif method == RetrievalMethod.KEYWORD:
            # Keyword retriever doesn't need additional special parameters
            logger.debug(f"Creating KeywordRetriever with params: {filtered_kwargs.keys()}")
            return KeywordRetriever(**filtered_kwargs)

        elif method == RetrievalMethod.ENSEMBLE:
            # Add ensemble-specific parameters
            if "weights" in kwargs:
                filtered_kwargs["weights"] = kwargs.get("weights")
            if "retrievers" in kwargs:
                filtered_kwargs["retrievers"] = kwargs.get("retrievers")
            logger.debug(f"Creating EnsembleSearchRetriever with params: {filtered_kwargs.keys()}")
            return EnsembleSearchRetriever(**filtered_kwargs)

        elif method == RetrievalMethod.HYBRID:
            # Add hybrid-specific parameters
            if "filter" in kwargs:
                filtered_kwargs["filter"] = kwargs.get("filter")
            if "prioritize_semantic" in kwargs:
                filtered_kwargs["prioritize_semantic"] = kwargs.get("prioritize_semantic")
            logger.debug(f"Creating HybridRetriever with params: {filtered_kwargs.keys()}")
            return HybridRetriever(**filtered_kwargs)

        elif method == RetrievalMethod.RERANKED:
            # Currently falling back to default as reranked isn't fully implemented
            logger.warning("RerankedRetriever not implemented, falling back to DefaultRetriever")
            return DefaultRetriever(**filtered_kwargs)

        else:  # Default
            logger.debug(f"Creating DefaultRetriever with params: {filtered_kwargs.keys()}")
            return DefaultRetriever(**filtered_kwargs)

    @staticmethod
    def from_config(config: Dict[str, Any] = None) -> BaseRetriever:
        """
        Create a retriever from configuration.

        Args:
            config: Configuration dictionary. Should contain:
                - method: The retrieval method to use
                - Other method-specific parameters

        Returns:
            A configured retriever instance
        """
        if not config:
            from simba.core.config import settings

            # Try to get retrieval config from settings
            if hasattr(settings, "retrieval") and hasattr(settings.retrieval, "method"):
                method = settings.retrieval.method
                logger.info(f"Creating retriever from config with method: {method}")

                # Extract other parameters
                params = {}
                if hasattr(settings.retrieval, "k"):
                    params["k"] = settings.retrieval.k

                # Get method-specific parameters
                if hasattr(settings.retrieval, "params"):
                    method_params = settings.retrieval.params
                    # Only add parameters that exist in the config
                    for key, value in method_params.items():
                        params[key] = value

                return RetrieverFactory.get_retriever(method, **params)

            # Fall back to default
            logger.info("No retrieval config found, using default retriever")
            return RetrieverFactory.get_retriever(RetrievalMethod.DEFAULT)

        # Create from provided config
        method = (
            config.pop("method", RetrievalMethod.DEFAULT)
            if isinstance(config, dict)
            else RetrievalMethod.DEFAULT
        )
        logger.info(f"Creating retriever with method: {method}")

        # Only pass config if it's a dictionary
        if isinstance(config, dict):
            return RetrieverFactory.get_retriever(method, **config)
        else:
            return RetrieverFactory.get_retriever(method)
