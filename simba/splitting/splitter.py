from typing import List, Optional

from langchain.schema import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid

from simba.core.factories.embeddings_factory import get_embeddings


class Splitter:
    def __init__(self, strategy: str = "recursive_character", chunk_size: int = 1500, chunk_overlap: int = 400):
        """
        Initialize a document splitter with configurable strategy and parameters.
        
        Args:
            strategy (str): The chunking strategy to use. Options:
                - "recursive_character": Simple chunking based on character count
                - "semantic_chunking": Chunks based on semantic shifts in content
                - "markdown_header": Splits by markdown headers, preserving document structure
                - "hierarchical": Splits text while respecting hierarchical structure
                - "context_aware": Enhanced recursive with larger overlap to preserve context
            chunk_size (int): Target size of each chunk
            chunk_overlap (int): Overlap between consecutive chunks to maintain context
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_document(self, documents: List[Document]) -> List[Document]:
        """
        Splits LangChain Documents into smaller chunks using the selected strategy.

        Args:
            documents (List[Document]): The LangChain Documents to split.

        Returns:
            List[Document]: A list of smaller Document chunks with preserved context.
        """
        # Check if input is a list and contains Document objects
        if not isinstance(documents, list) or not all(
            isinstance(doc, Document) for doc in documents
        ):
            raise ValueError("Input must be a list of LangChain Document objects")

        # Choose splitting strategy
        if self.strategy == "recursive_character":
            return self.recursive_character_text_splitter(documents)
        elif self.strategy == "semantic_chunking":
            return self.semantic_chunking(documents)
        elif self.strategy == "markdown_header":
            return self.markdown_header_splitter(documents)
        elif self.strategy == "hierarchical":
            return self.hierarchical_splitter(documents)
        elif self.strategy == "context_aware":
            return self.context_aware_splitter(documents)
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")

    def recursive_character_text_splitter(self, documents: List[Document]) -> List[Document]:
        """Standard recursive character splitting"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
        documents= text_splitter.split_documents(documents)
        for doc in documents:
            doc.id = str(uuid.uuid4())

        return documents


    def semantic_chunking(self, documents: List[Document]) -> List[Document]:
        """Split based on semantic shifts in content"""
        embedder = get_embeddings()
        splitter = SemanticChunker(
            embedder,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=0.8,
        )
        
        all_chunks = []
        for doc in documents:
            chunks = splitter.create_documents(doc.page_content)
            # Preserve metadata from parent document
            for chunk in chunks:
                chunk.metadata.update(doc.metadata)
            all_chunks.extend(chunks)
            
        return all_chunks

    