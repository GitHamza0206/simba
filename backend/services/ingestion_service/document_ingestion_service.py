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

    def ingest_document(self, file: UploadFile , 
                        folder_path: str = settings.paths.upload_dir,
                        store_locally: bool = True) -> Document:
        """
        Process and ingest documents into the vector store.
        
        Args:
            file: UploadFile to ingest
            
        Returns:
            Document: The ingested document
        """
        try:
            logger.info(f"Starting ingestion of {file.filename}")

            # Create relative paths instead of absolute paths
           
            folder_path = Path(folder_path)
            

            
            file_extension = f".{file.filename.split('.')[-1].lower()}" 
            loader = SUPPORTED_EXTENSIONS[file_extension]

            # Create a temporary file and save the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                file.file.seek(0)
                content = file.file.read()
                temp_file.write(content)
                temp_path = temp_file.name
                file.file.seek(0)

            try:
                document = loader(temp_path).load()
                
                # Format size in a human-readable format
                size_in_mb = round(len(content) / (1024 * 1024), 2)
                size_str = f"{size_in_mb} MB"
                
                metadata = MetadataType(
                    filename=file.filename,
                    type=file_extension,
                    size=size_str,
                    loader=loader.__name__,
                    uploadedAt=datetime.now().isoformat(),
                    file_path=str(folder_path / file.filename),
                    parser=None
                )
                document[0].metadata = metadata.dict()

                # Pass the Path object for saving
                if store_locally:
                    save_file_locally(file, folder_path)

                # Add to vector store and get the document back
                ingested_doc = self.vector_store.add_documents(document)[0]
                
                # Create and return IngestedDocument
                return ingested_doc

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            raise e
        
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by its ID"""
        try:
            document = self.vector_store.get_document(document_id)
            if not document:
                logger.warning(f"Document {document_id} not found in vector store")
                return None
            return document
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None

    def delete_ingested_document(self, uid: str) -> int:
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
                # Format size as string if it's a number
                size = doc.metadata.get('size', 'unknown')
                if isinstance(size, (int, float)):
                    size_in_mb = round(size / (1024 * 1024), 2)
                    size = f"{size_in_mb} MB"

                # Set default metadata values
                default_metadata = {
                    'filename': os.path.basename(doc.metadata.get('filename', 'unknown')),
                    'size': size,
                    'type': doc.metadata.get('type', 'unknown'),
                    'loader': doc.metadata.get('loader', 'unknown'),
                    'parser': doc.metadata.get('parser', 'not needed'),
                    'uploadedAt': doc.metadata.get('uploadedAt', datetime.now().isoformat()),
                    'file_path': doc.metadata.get('file_path', doc.metadata.get('filename', 'unknown'))
                }

                # Create metadata object
                metadata = MetadataType(**default_metadata)

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


