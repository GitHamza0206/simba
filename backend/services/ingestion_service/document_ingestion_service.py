import logging
import io
from pathlib import Path
from typing import List, Optional
import uuid
from core.factories.database_factory import get_database
from langchain.schema import Document
from core.config import settings
import os 
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from fastapi import UploadFile
import aiofiles
import asyncio

from services.ingestion_service.file_handling import delete_file_locally, save_file_locally
from services.splitter import split_document
from services.vector_store_service import VectorStoreService
import tempfile

from datetime import datetime
from services.ingestion_service.types import MetadataType, IngestedDocument, SimbaDoc
from services.ingestion_service.config import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.database = get_database()

    async def ingest_document(self, file: UploadFile) -> Document:
        """
        Process and ingest documents into the vector store.
        
        Args:
            file: UploadFile to ingest
            
        Returns:
            Document: The ingested document
        """
        
        try:
            folder_path = Path(settings.paths.upload_dir)
            file_path = folder_path / file.filename
            file_extension = f".{file.filename.split('.')[-1].lower()}" 
            loader = SUPPORTED_EXTENSIONS[file_extension]
            
            # Ensure file exists and is not empty
            if not file_path.exists():
                raise ValueError(f"File {file_path} does not exist")
                
            if file_path.stat().st_size == 0:
                raise ValueError(f"File {file_path} is empty")
            
            # Use asyncio.to_thread for synchronous loader
            document = await asyncio.to_thread(lambda: loader(file_path=str(file_path)).load())
            
            # Use aiofiles for async file size check
            async with aiofiles.open(file_path, 'rb') as f:
                await f.seek(0, 2)  # Seek to end of file
                file_size = await f.tell()  # Get current position (file size)
                
            size_str = f"{file_size / (1024 * 1024):.2f} MB"    
            
            metadata = MetadataType(
                filename=file.filename,
                type=file_extension,
                page_number=len(document),
                chunk_number=0,
                enabled=False,
                parsing_status="Unparsed",
                size=size_str,
                loader=loader.__name__,
                uploadedAt=datetime.now().isoformat(),
                file_path=str(file_path),
                parser=None
            )
            
   
            return SimbaDoc.from_documents(id=str(uuid.uuid4()), documents=document, metadata=metadata)
        
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

    def delete_ingested_document(self, uid: str, delete_locally: bool = False) -> int:
        try:
            
            if delete_locally:
                doc = self.vector_store.get_document(uid)   
                delete_file_locally(Path(doc.metadata.get('file_path')))

            self.vector_store.delete_documents([uid])

            return {"message": f"Document {uid} deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting document {uid}: {e}")
            raise e
        
    def get_ingested_documents_by_folder(self) -> dict:
        documents_dict = {}
        try:
            uploads_dir = settings.paths.upload_dir
            for root, _, files in os.walk(uploads_dir):
                for file in files:
                    file_extension = f".{file.split('.')[-1].lower()}" 
                    if file.endswith(".md"):
                        loader = SUPPORTED_EXTENSIONS[file_extension]
                        doc_id = str(uuid.uuid4())
                        file_path = os.path.join(root, file)
                        document = loader(file_path).load()[0]
                        documents_dict[doc_id] = IngestedDocument(
                            id=doc_id,
                            page_content=document.page_content,
                            metadata=MetadataType(
                                filename=file,
                                type=file.split(".")[-1],
                                size= "100 MB",
                                loader=loader.__name__,
                                uploadedAt=datetime.now().isoformat(),
                                file_path=file_path,
                                parser=None
                            )
                        )


            return documents_dict

        except Exception as e:
            logger.error(f"Error getting ingested documents by folder: {e}")
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

        for root, _, files in os.walk(settings.paths.upload_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    md_files.append(file_path)


        docs = [SUPPORTED_EXTENSIONS[".md"](file_path).load() for file_path in md_files]
        # docs = [CustomMarkdownLoader(url[1]).load() for url in urls]
        docs_list = [item for sublist in docs for item in sublist]

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.chunking.chunk_size, chunk_overlap=settings.chunking.chunk_overlap
        )
        
        doc_splits = text_splitter.split_documents(docs_list) #TODO Chunking strategy choose
            
        self.vector_store.add_documents(doc_splits)
        
        

if __name__ == "__main__":
    document_ingestion_service = DocumentIngestionService()


