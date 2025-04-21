import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import UploadFile
from langchain.schema import Document

from simba.core.config import settings
from simba.core.factories.database_factory import get_database
from simba.core.factories.vector_store_factory import VectorStoreFactory
from simba.models.simbadoc import MetadataType, SimbaDoc
from simba.splitting import Splitter
from simba.core.factories.storage_factory import StorageFactory
from simba.storage.base import StorageProvider
from simba.core.redis import RedisService
from .loader import Loader
from .file_handling import delete_file_locally

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Service for ingesting documents"""
    
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.database = get_database()
        self.loader = Loader()
        self.splitter = Splitter()
        self.storage: StorageProvider = StorageFactory.get_storage_provider()
        self.redis = RedisService()

    async def ingest_document(self, file: UploadFile, folder_path: str = "/") -> SimbaDoc:
        """Ingest a document
        
        Args:
            file: The file to ingest
            folder_path: The folder path to store the document
            
        Returns:
            SimbaDoc: The ingested document
        """
        try:
            # Generate file path
            file_path = Path(folder_path.strip("/")) / file.filename
            file_extension = f".{file.filename.split('.')[-1].lower()}"
            
            # Save file using storage provider
            saved_path = await self.storage.save_file(file_path, file)
            
            # Get file size
            file_size = saved_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"File {saved_path} is empty")
            
            # Load and process document
            document = await self.loader.aload(file_path=str(saved_path))
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
                file_path=str(saved_path),
                parser=None,
            )
            
            # Create SimbaDoc
            simbadoc = SimbaDoc.from_documents(
                id=str(uuid.uuid4()), documents=document, metadata=metadata
            )
            
            # Cache the document in Redis
            await self.redis.set(f"documents:{simbadoc.id}", simbadoc.dict())
            
            return simbadoc
            
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            # Clean up file if ingestion fails
            if 'saved_path' in locals():
                await self.storage.delete_file(saved_path)
            raise

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by its ID"""
        try:
            # Try to get from Redis first
            cached_doc = await self.redis.get(f"documents:{document_id}")
            if cached_doc:
                return Document(**cached_doc)
                
            # If not in Redis, get from vector store
            document = self.vector_store.get_document(document_id)
            if document:
                # Cache in Redis
                await self.redis.set(f"documents:{document_id}", document.dict())
            return document
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None

    async def delete_ingested_document(self, uid: str, delete_locally: bool = False) -> int:
        try:
            if delete_locally:
                doc = self.vector_store.get_document(uid)
                delete_file_locally(Path(doc.metadata.get("file_path")))

            self.vector_store.delete_documents([uid])
            
            # Delete from Redis cache
            await self.redis.delete(f"documents:{uid}")

            return {"message": f"Document {uid} deleted successfully"}

        except Exception as e:
            logger.error(f"Error deleting document {uid}: {e}")
            raise e

    async def update_document(self, simbadoc: SimbaDoc, args: dict):
        try:
            for key, value in args.items():
                setattr(simbadoc.metadata, key, value)

            self.vector_store.update_document(simbadoc.id, simbadoc)
            
            # Update Redis cache
            await self.redis.set(f"documents:{simbadoc.id}", simbadoc.dict())
            
            logger.info(f"Document {simbadoc.id} updated successfully")
        except Exception as e:
            logger.error(f"Error updating document {simbadoc.id}: {e}")
            raise e
