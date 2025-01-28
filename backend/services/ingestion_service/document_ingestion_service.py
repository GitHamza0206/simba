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

from services.vector_store_service import VectorStoreService
import tempfile

from datetime import datetime
from services.ingestion_service.types import MetadataType, SimbaDoc
from services.loader import Loader
logger = logging.getLogger(__name__)

class DocumentIngestionService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.database = get_database()
        self.loader = Loader()

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

            
            # Ensure file exists and is not empty
            if not file_path.exists():
                raise ValueError(f"File {file_path} does not exist")
                
            if file_path.stat().st_size == 0:
                raise ValueError(f"File {file_path} is empty")
            

            # Use asyncio.to_thread for synchronous loader
            document = await self.loader.aload(file_path=str(file_path))
            
            # Set id for each Document in the list
            for doc in document:
                doc.id = str(uuid.uuid4())
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
                loader=self.loader.__name__,
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
        
    
        
    

    def update_document(self, simbadoc: SimbaDoc, args: dict):
        try:
            for key, value in args.items():
                setattr(simbadoc.metadata, key, value)

            self.vector_store.update_document(simbadoc.id, simbadoc)
            logger.info(f"Document {simbadoc.id} updated successfully")
        except Exception as e:
            logger.error(f"Error updating document {simbadoc.id}: {e}")
            raise e

    def sync_with_store(self):
        """Sync embedding status with vector store"""
        try:
            store_documents: List[Document] = self.vector_store.get_documents()
            db_docs: List[SimbaDoc] = self.database.get_all_documents()
            
            for simba_doc in db_docs:
                if simba_doc.metadata.enabled:
                    # Check if simba_doc's documents exist in store
                    docs_found = any(
                        store_doc.metadata.get('doc_id') == simba_doc.id 
                        for store_doc in store_documents
                    )
                    
                    if not docs_found:
                        logger.warning(f"Documents for SimbaDoc {simba_doc.id} not found in store. Disabling.")
                        simba_doc.metadata.enabled = False
                        self.database.update_document(simba_doc.id, simba_doc)
                
                else:
                    docs_found = any(
                        store_doc.metadata.get('doc_id') == simba_doc.id 
                        for store_doc in store_documents
                    )
                    
                    if docs_found:
                        logger.info(f"Documents for SimbaDoc {simba_doc.id} found in store. Enabling.")
                        simba_doc.metadata.enabled = True
                        self.database.update_document(simba_doc.id, simba_doc)
            
            logger.info("Store synchronization completed")
            
        except Exception as e:
            logger.error(f"Error syncing with store: {e}")
            raise e

if __name__ == "__main__":
    document_ingestion_service = DocumentIngestionService()
    #document_ingestion_service.sync_with_store()


