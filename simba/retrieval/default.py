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
                
        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", self.default_k)
        return self.store.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": k}
        ).get_relevant_documents(query) 