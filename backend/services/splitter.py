from typing import List
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_document(documents: List[Document]) -> List[Document]:
    """
    Splits a LangChain Document into smaller chunks.
    
    Args:
        document (Document): The LangChain Document to split.
        
    Returns:
        List[Document]: A list of smaller Document chunks.
    """
    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=400)  # TODO: Make these parameters configurable
    
    # Check if input is a list and contains Document objects
    if not isinstance(documents, list) or not all(isinstance(doc, Document) for doc in documents):
        raise ValueError("Input must be a list of LangChain Document objects")
    
    # Split the documents into chunks
    chunks = text_splitter.split_documents(documents)
    
    return chunks