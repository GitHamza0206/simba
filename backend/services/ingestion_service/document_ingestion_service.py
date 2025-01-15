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

from services.ingestion_service.file_handling import save_file_locally
from services.vector_store_service import VectorStoreService
import tempfile

from datetime import datetime
from services.ingestion_service.types import MetadataType, IngestedDocument
from services.ingestion_service.config import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    def __init__(self):
        self.vector_store = VectorStoreService()

    def ingest_document(self, file: UploadFile):
        """
        Process and ingest documents into the vector store.
        
        Args:
            file: UploadFile to ingest
            
        Returns:
            int: Number of documents successfully ingested
        """
        try:
            logger.info(f"Starting ingestion of {file.filename}")
            file_extension = f".{file.filename.split('.')[-1].lower()}" 
            loader = SUPPORTED_EXTENSIONS[file_extension]

            # Create a temporary file and save the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                # Reset file pointer to beginning
                file.file.seek(0)
                
                # Copy content to temporary file
                content = file.file.read()
                temp_file.write(content)
                temp_path = temp_file.name

                # Reset file pointer for potential future use
                file.file.seek(0)

            try:
                # Load document using the appropriate loader
                document = loader(temp_path).load()
                
                # Create metadata
                metadata = MetadataType(
                    filename=file.filename,
                    type=file.content_type,
                    size=len(content),  # Use the content length we already have
                    loader=loader.__name__,
                    uploadedAt=datetime.now().isoformat(),
                    file_path=temp_path,
                    parser=None
                )
                document[0].metadata = metadata.dict()

                # Save file locally with metadata
                save_file_locally(file)

                # Add to vector store
                self.vector_store.add_documents(document)
                count = self.vector_store.count_documents()
                logger.info(f"Successfully ingested documents. Total count: {count}")
                return count

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            raise e

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
        all_documents = self.vector_store.get_documents()
        documents_dict = {}
        
        for doc in all_documents:
            try:
                # Convert size to int if it exists
                if 'size' in doc.metadata:
                    doc.metadata['size'] = int(doc.metadata['size'])

                # Set default metadata values
                default_metadata = {
                    'filename': os.path.basename(doc.metadata['filename']),
                    'type': 'unknown',
                    'loader': 'unknown',
                    'uploadedAt': datetime.now().isoformat(),
                    'file_path': doc.metadata['filename']
                }

                # Merge with existing metadata, giving priority to existing values
                metadata = MetadataType(**{**default_metadata, **doc.metadata})

                documents_dict[doc.id] = IngestedDocument(
                    id=doc.id,
                    page_content=doc.page_content,
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}")
                continue
        
        return documents_dict

    def update_document(self, document_id: str, newDocument: Document):
        try:
            self.vector_store.update_document(document_id, newDocument)
            logger.info(f"Document {document_id} updated successfully")
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            raise e


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

        
        docs = [SUPPORTED_EXTENSIONS[".md"](url[1]).load() for url in md_files]
        # docs = [CustomMarkdownLoader(url[1]).load() for url in urls]
        docs_list = [item for sublist in docs for item in sublist]

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.chunking.chunk_size, chunk_overlap=settings.chunking.chunk_overlap
        )
        
        doc_splits = text_splitter.split_documents(docs_list) #TODO Chunking strategy choose
        
        self.ingest_documents(docs_list)
        
        

if __name__ == "__main__":
    document_ingestion_service = DocumentIngestionService()


