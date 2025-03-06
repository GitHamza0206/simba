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

from .file_handling import delete_file_locally
from .loader import Loader

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_vector_store()
        self.database = get_database()
        self.loader = Loader()
        self.splitter = Splitter()

    async def ingest_document(self, file: UploadFile, file_path: Optional[str] = None) -> Document:
        """
        Process and ingest documents into the vector store.

        Args:
            file: UploadFile to ingest
            file_path: Optional explicit file path to use instead of the default upload path

        Returns:
            Document: The ingested document
        """
        try:
            # Additional logging to trace issues
            logger.info(f"Starting document ingestion for file: {file.filename}, path: {file_path}")
            
            folder_path = Path(settings.paths.upload_dir)
            
            # Validate file_path - robust validation
            if file_path is None or file_path == "None" or file_path == "":
                error_msg = f"Invalid file path '{file_path}' for file {file.filename}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Normalize path handling - ensure it's a Path object
            try:
                if isinstance(file_path, str):
                    path_obj = Path(file_path)
                else:
                    path_obj = file_path
                    
                # Make absolute if relative
                if not path_obj.is_absolute():
                    path_obj = path_obj.resolve()
                    
                file_path = path_obj
                
                # Log the normalized path
                logger.debug(f"Normalized file path: {file_path}")
                
            except Exception as e:
                logger.error(f"Error normalizing file path {file_path}: {str(e)}")
                raise ValueError(f"Invalid file path format: {str(e)}")
                
            # Ensure file exists before attempting to open
            if not file_path.exists():
                error_msg = f"File does not exist at path: {file_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            file_extension = f".{file.filename.split('.')[-1].lower()}"

            # Log before attempting to open file
            logger.info(f"Attempting to open file at {file_path}")
            
            # Get file info and validate in one async operation - robust error handling
            try:
                async with aiofiles.open(str(file_path), "rb") as f:
                    await f.seek(0, 2)  # Seek to end
                    file_size = await f.tell()

                    if file_size == 0:
                        raise ValueError(f"File {file_path} is empty")
                        
                    # Reset to beginning for subsequent operations
                    await f.seek(0)
                    
                logger.debug(f"Successfully opened and checked file: {file_path}, size: {file_size}")
            except FileNotFoundError:
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                raise
            except Exception as e:
                error_msg = f"Error opening file {file_path}: {str(e)}"
                logger.error(error_msg)
                raise

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
                parser=None,
            )

            return SimbaDoc.from_documents(
                id=str(uuid.uuid4()), documents=document, metadata=metadata
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
                delete_file_locally(Path(doc.metadata.get("file_path")))

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
