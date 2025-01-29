import logging
from pathlib import Path
from typing import Optional
import uuid
from core.factories.database_factory import get_database
from langchain.schema import Document
from core.config import settings
from fastapi import UploadFile
import aiofiles

from services.ingestion_service.file_handling import delete_file_locally

from services.vector_store_service import VectorStoreService
from services.splitter import Splitter
from datetime import datetime
from services.loader import Loader
from models.simbadoc import SimbaDoc, MetadataType


logger = logging.getLogger(__name__)

class DocumentIngestionService:
    def __init__(self):
        self.vector_store = VectorStoreService()
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

            
            # Ensure file exists and is not empty
            if not file_path.exists():
                raise ValueError(f"File {file_path} does not exist")
                
            if file_path.stat().st_size == 0:
                raise ValueError(f"File {file_path} is empty")
            

            # Use asyncio.to_thread for synchronous loader
            document = await self.loader.aload(file_path=str(file_path))
            document = self.splitter.split_document(document) #split document into chunks
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
            # Get all documents from database
            db_docs = self.database.get_all_documents()

            # Get IDs for comparison
            kms_chunks_id = [chunk.id for simba_doc in db_docs for chunk in simba_doc.documents]
            store_chunks_id = [doc.id for doc in store_documents]
            orphaned_chunks = set(store_chunks_id) - set(kms_chunks_id)

            logger.info(f"KMS chunks: {kms_chunks_id}")
            logger.info(f"Store chunks: {store_chunks_id}")
            logger.info(f"Orphaned chunks: {orphaned_chunks}")

            # Delete orphaned chunks from store
            if orphaned_chunks:
                logger.warning(f"Deleting orphaned chunks: {orphaned_chunks}")
                self.vector_store.delete_documents(list(orphaned_chunks))

            # Track documents that need updates
            updates_needed = []

            # Update document states based on their chunks in store
            for simba_doc in db_docs:
                doc_chunks = set(chunk.id for chunk in simba_doc.documents)
                chunks_in_store = doc_chunks.intersection(set(store_chunks_id))
                
                if len(chunks_in_store) == len(doc_chunks):
                    # All chunks are in store - document should be enabled
                    if not simba_doc.metadata.enabled:
                        logger.info(f"Enabling document {simba_doc.id} - all chunks found in store")
                        simba_doc.metadata.enabled = True
                        updates_needed.append(simba_doc)
                else:
                    # Not all chunks are in store - document should be disabled
                    if simba_doc.metadata.enabled:
                        logger.warning(f"Disabling document {simba_doc.id} - missing chunks in store")
                        simba_doc.metadata.enabled = False
                        updates_needed.append(simba_doc)
                        # Delete any remaining chunks from store
                        if chunks_in_store:
                            logger.info(f"Deleting remaining chunks for disabled document: {chunks_in_store}")
                            self.vector_store.delete_documents(list(chunks_in_store))

            # Perform all database updates
            for doc in updates_needed:
                logger.info(f"Updating document {doc.id} enabled status to {doc.metadata.enabled}")
                success = self.database.update_document(doc.id, doc)
                if not success:
                    logger.error(f"Failed to update document {doc.id}")
                    raise ValueError(f"Failed to update document {doc.id}")

            # Verify updates
            for doc in updates_needed:
                verified_doc = self.database.get_document(doc.id)
                if verified_doc.metadata.enabled != doc.metadata.enabled:
                    logger.error(f"Document {doc.id} failed to update. Expected enabled={doc.metadata.enabled}, got {verified_doc.metadata.enabled}")
                    raise ValueError(f"Document {doc.id} failed to update correctly")

            # Final verification of store state
            store_documents_after = self.vector_store.get_documents()
            store_chunks_after = set(doc.id for doc in store_documents_after)
            
            # Verify no orphaned chunks remain
            remaining_orphans = store_chunks_after - set(kms_chunks_id)
            if remaining_orphans:
                logger.error(f"Orphaned chunks still present after sync: {remaining_orphans}")
                raise ValueError(f"Failed to remove all orphaned chunks: {remaining_orphans}")

            logger.info("Store synchronization completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during store synchronization: {e}")
            raise e

if __name__ == "__main__":
    kms = DocumentIngestionService()
    kms.sync_with_store()


