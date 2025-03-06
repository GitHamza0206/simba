"""
Hybrid retriever that combines and post-processes results from multiple methods.
"""
from typing import List, Optional

from langchain.schema import Document

from simba.retrieval.base import BaseRetriever
from simba.vector_store import VectorStoreService


class HybridRetriever(BaseRetriever):
    """Hybrid retriever that combines and post-processes results from multiple methods."""
    
    def __init__(self, vector_store: Optional[VectorStoreService] = None, prioritize_semantic: bool = True, **kwargs):
        """
        Initialize the hybrid retriever.
        
        Args:
            vector_store: Optional vector store to use
            prioritize_semantic: Whether to prioritize semantic results over keyword results
            **kwargs: Additional parameters
        """
        super().__init__(vector_store)
        self.prioritize_semantic = prioritize_semantic
    
    def retrieve(self, query: str, **kwargs) -> List[Document]:
        """
        Retrieve documents using a custom hybrid approach that combines
        multiple retrieval strategies and post-processes the results.
        
        Args:
            query: The query string
            **kwargs: Additional parameters including:
                - k: Number of documents to retrieve (default: 5)
                - filter: Metadata filters to apply
                - prioritize_semantic: Whether to prioritize semantic results (overrides instance setting)
                
        Returns:
            List of relevant documents
        """
        k = kwargs.get("k", 5)
        filter_dict = kwargs.get("filter", None)
        prioritize_semantic = kwargs.get("prioritize_semantic", self.prioritize_semantic)
        
        # Import here to avoid circular import
        from simba.retrieval.default import DefaultRetriever
        from simba.retrieval.semantic import SemanticRetriever
        
        # Get documents from different retrieval methods
        default_retriever = DefaultRetriever(self.store)
        semantic_retriever = SemanticRetriever(self.store)
        
        default_docs = default_retriever.retrieve(query, k=k*2, filter=filter_dict)
        semantic_docs = semantic_retriever.retrieve(query, k=k*2, filter=filter_dict)
        
        # Combine results (removing duplicates)
        combined_docs = []
        seen_contents = set()
        
        # Determine order based on prioritization
        if prioritize_semantic:
            primary_docs = semantic_docs
            secondary_docs = default_docs
        else:
            primary_docs = default_docs
            secondary_docs = semantic_docs
        
        # Process both result sets, prioritizing primary docs
        for doc in primary_docs + secondary_docs:
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