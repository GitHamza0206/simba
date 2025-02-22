import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import asyncio

import aiofiles
from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from fastapi import UploadFile
from langchain.schema import Document
from simba.models.simbadoc import MetadataType, SimbaDoc

from .loader import Loader
from .file_handling import delete_file_locally
from .utils import check_file_exists
from simba.splitting import Splitter

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.database = get_database()
        self.loader = Loader()
        self.splitter = Splitter()

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

            # Get file info and validate in one async operation
            async with aiofiles.open(file_path, 'rb') as f:
                await f.seek(0, 2)  # Seek to end
                file_size = await f.tell()
                
                if file_size == 0:
                    raise ValueError(f"File {file_path} is empty")

            # Load and process document
            document = await self.loader.aload(file_path=str(file_path))
            document = await asyncio.to_thread(self.splitter.split_document, document)
            
            # Set unique IDs for chunks
            for doc in document:
                doc.id = str(uuid.uuid4())
            
            # Create metadata
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
            
            return SimbaDoc.from_documents(
                id=str(uuid.uuid4()), 
                documents=document, 
                metadata=metadata
            )
        
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

    




