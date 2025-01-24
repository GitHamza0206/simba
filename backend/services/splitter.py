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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)  # TODO: Make these parameters configurable
    
    # Ensure the input is a Document object
    if not isinstance(documents, List[Document]):
        raise ValueError("Input must be a LangChain Document object.")
    
    # Split the document's page_content into chunks
    chunks = text_splitter.split_documents(documents)  # Pass a list containing the Document object
    
    return chunks