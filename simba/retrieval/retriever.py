from enum import Enum
from typing import Any, Dict, List, Optional, Union

from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document
from langchain_community.retrievers import BM25Retriever

from simba.core.factories.vector_store_factory import VectorStoreFactory


class RetrievalMethod(str, Enum):
    DEFAULT = "default"
    ENSEMBLE = "ensemble"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class Retriever:
    def __init__(self):
        self.store = VectorStoreFactory.get_vector_store()

    def retrieve(
        self, query: str, method: Union[str, RetrievalMethod] = RetrievalMethod.DEFAULT, **kwargs
    ) -> List[Document]:
        """
        Retrieve documents using the specified method.

        Args:
            query: The query string
            method: Retrieval method to use
            **kwargs: Additional parameters for the retrieval method

        Returns:
            List of relevant documents
        """
        # Convert string to enum if needed
        if isinstance(method, str):
            method = RetrievalMethod(method)

        # Choose the appropriate retrieval method
        if method == RetrievalMethod.ENSEMBLE:
            return self._retrieve_ensemble(query, **kwargs)
        elif method == RetrievalMethod.SEMANTIC:
            return self._retrieve_semantic(query, **kwargs)
        elif method == RetrievalMethod.HYBRID:
            return self._retrieve_hybrid(query, **kwargs)
        else:  # Default
            return self._retrieve_default(query, **kwargs)

    def _retrieve_default(self, query: str, **kwargs) -> List[Document]:
        k = kwargs.get("k", 5)
        return self.store.as_retriever(
            search_type="similarity", search_kwargs={"k": k}
        ).get_relevant_documents(query)

    def _retrieve_ensemble(self, query: str, **kwargs) -> List[Document]:
        ensemble = self.as_ensemble_retriever()
        return ensemble.get_relevant_documents(query)

    def _retrieve_semantic(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieve documents using semantic search with configurable thresholds.

        Args:
            query: The query string
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve
                - score_threshold: Minimum similarity score to include a document
                - filter: Metadata filters to apply to the search

        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", 5)
        score_threshold = kwargs.get("score_threshold", 0.5)
        filter_dict = kwargs.get("filter", None)

        return self.store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": k, "score_threshold": score_threshold, "filter": filter_dict},
        ).get_relevant_documents(query)

    def _retrieve_hybrid(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieve documents using a custom hybrid approach that combines
        multiple retrieval strategies and post-processes the results.

        Args:
            query: The query string
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve
                - reranker_threshold: Threshold for reranking
                - filter: Metadata filters to apply

        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", 5)
        filter_dict = kwargs.get("filter", None)

        # Get documents from different retrieval methods
        default_docs = self._retrieve_default(query, k=k * 2, filter=filter_dict)
        semantic_docs = self._retrieve_semantic(query, k=k * 2, filter=filter_dict)

        # Combine results (removing duplicates)
        combined_docs = []
        seen_contents = set()

        # Process both result sets, prioritizing semantic results
        for doc in semantic_docs + default_docs:
            # Create a hash of the content to identify duplicates
            # Using a substring to avoid excessive memory usage for large docs
            content_hash = hash(doc.page_content[:100])

            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                combined_docs.append(doc)

                # Stop when we have enough documents
                if len(combined_docs) >= k:
                    break

        return combined_docs

    def as_retriever(self, **kwargs):
        return self.store.as_retriever(**kwargs)

    def as_ensemble_retriever(self):
        documents = self.store.get_documents()

        self.store.save()

        retriever = self.store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        keyword_retriever = BM25Retriever.from_documents(
            documents,
            preprocess_func=lambda text: text.lower(),  # Simple preprocessing
        )
        return EnsembleRetriever(retrievers=[retriever, keyword_retriever], weights=[0.7, 0.3])
