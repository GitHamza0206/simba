from typing import List

from simba.core.factories.embeddings_factory import get_embeddings
from langchain.schema import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Splitter:
    def __init__(self):

        self.strategy = "recursive_character" # TODO: Make this configurable

    
    def split_document(self, documents: List[Document]) -> List[Document]:
        """
        Splits a LangChain Document into smaller chunks.
        
        Args:
            document (Document): The LangChain Document to split.
            
        Returns:
            List[Document]: A list of smaller Document chunks.
        """
        # Initialize the text splitter

        if self.strategy == "recursive_character":
            return self.recursive_character_text_splitter(documents)
        elif self.strategy == "semantic_chunking":
            return self.semantic_chunking(documents)
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")

    
    def recursive_character_text_splitter(self, documents: List[Document]) -> List[Document]:
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=400)  # TODO: Make these parameters configurable
        
        # Check if input is a list and contains Document objects
        if not isinstance(documents, list) or not all(isinstance(doc, Document) for doc in documents):
            raise ValueError("Input must be a list of LangChain Document objects")
        
        # Split the documents into chunks
        chunks = text_splitter.split_documents(documents)
        
        return chunks
    
    def semantic_chunking(self, documents: List[Document]) -> List[Document]:
        
        embedder = get_embeddings()
        splitter = SemanticChunker(
            embedder,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=0.8
        )
        return splitter.create_documents(documents[0].page_content)