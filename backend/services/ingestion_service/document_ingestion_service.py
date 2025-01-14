import logging
import io
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document
from core.config import settings
import os 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from fastapi import UploadFile
from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader,
)
from services.vector_store_service import VectorStoreService
import tempfile
from services.ingestion_service.utils import get_file_size_mb
import json
from datetime import datetime
logger = logging.getLogger(__name__)

class IngestedDocument(BaseModel):
    id: str
    page_content: str
    metadata: dict

    def to_dict(self):
        return json.dumps({
            "id": self.id,
            "page_content": self.page_content,
            "metadata": self.metadata
        })

class DocumentIngestionService:

    SUPPORTED_EXTENSIONS = {
        ".md": UnstructuredMarkdownLoader,
        ".pdf": UnstructuredPDFLoader,
        ".pptx": UnstructuredPowerPointLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".docx": UnstructuredWordDocumentLoader,
    }



    def __init__(self):
        self.vector_store = VectorStoreService()

    def delete_ingested_document(self, uid: str):
        try:
            self.vector_store.delete_documents([uid])
            count = self.vector_store.count_documents()
            logger.info(f"Document {uid} deleted successfully")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting document {uid}: {e}")
            raise e

    def get_ingested_documents(self) -> dict:
        #this function should return documents from the vector store
        #it should be loaded in a format that can be used by the frontend 
        #we should store the document in raw format and also in the vector store 

        # Access the internal docstore and index_to_docstore_id mapping
        all_documents = self.vector_store.get_documents()

        documents_dict = {}
        for doc in all_documents:
            doc_id = doc.id

            page_content = doc.page_content
            metadata = doc.metadata
            documents_dict[doc_id] = IngestedDocument(
                id=doc_id,
                page_content=page_content,
                metadata=metadata
            )
        
        return documents_dict
            

    
    def ingest_document(self, file: UploadFile):
        """
        Process and ingest documents into the vector store.
        
        Args:
            documents: List of documents to ingest
            
        Returns:
            int: Number of documents successfully ingested
        """
        try:
            logger.info(f"Starting ingestion of {file.filename}")
            file_extension = f".{file.filename.split('.')[-1].lower()}" 
            loader = self.SUPPORTED_EXTENSIONS[file_extension]
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file.file.read())
                temp_path = temp_file.name

            try:
                document = loader(temp_path).load()
                document[0].metadata['filename'] = file.filename
                document[0].metadata['type'] = file.content_type
                file_size_mb = get_file_size_mb(file)
                document[0].metadata['size'] = file_size_mb
                document[0].metadata['loader'] = loader.__name__
                document[0].metadata['uploadedAt'] = datetime.now().isoformat()
            finally:
                # Nettoyer le fichier temporaire
                os.unlink(temp_path)
            

            self.vector_store.add_documents(document)
            count = self.vector_store.count_documents()
            logger.info(f"Successfully ingested documents. Total count: {count}")
            return count
        except Exception as e:
            return {"message": "Error ingesting document"}





    def ingest_markdowns_from_dir(self):
        """
        Ingest all documents from a directory.
        
        Args:
            directory: Path to directory containing documents
            
        Returns:
            int: Number of documents ingested
        """
        # Implementation for directory processing
    
        """
        Retrieve all .md files from a given folder, including subfolders.
        Returns a list of tuples containing the folder name and file path for each .md file.
        """

        md_files = []

        for root, _, files in os.walk(settings.paths.markdown_dir):
            folder_name = os.path.basename(root)
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    md_files.append((folder_name, file_path))

        
        docs = [UnstructuredMarkdownLoader(url[1]).load() for url in md_files]
        # docs = [CustomMarkdownLoader(url[1]).load() for url in urls]
        docs_list = [item for sublist in docs for item in sublist]

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.chunking.chunk_size, chunk_overlap=settings.chunking.chunk_overlap
        )
        
        doc_splits = text_splitter.split_documents(docs_list) #TODO Chunking strategy choose
        
        self.ingest_documents(docs_list)
        
        

if __name__ == "__main__":
    document_ingestion_service = DocumentIngestionService()


