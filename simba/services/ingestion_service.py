"""Document ingestion service - orchestrates the full pipeline."""

import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from simba.models import Document
from simba.services import (
    chunker_service,
    embedding_service,
    parser_service,
    qdrant_service,
    storage_service,
)

logger = logging.getLogger(__name__)


def ingest_document(document_id: str, db: Session) -> None:
    """Process a document through the full ingestion pipeline.

    Pipeline steps:
    1. Download file from MinIO
    2. Parse document to extract text
    3. Chunk text into smaller pieces
    4. Generate embeddings for each chunk
    5. Store embeddings in Qdrant

    Args:
        document_id: ID of the document to process.
        db: Database session.

    Raises:
        Exception: If any step in the pipeline fails.
    """
    # Get document from database
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document not found: {document_id}")

    try:
        # Update status to processing
        document.status = "processing"
        db.commit()

        logger.info(f"Starting ingestion for document {document_id}: {document.name}")

        # Step 1: Download file from MinIO
        logger.info(f"Downloading file from MinIO: {document.object_key}")
        file_content = storage_service.download_file(document.object_key)

        # Step 2: Parse document
        logger.info(f"Parsing document: {document.name}")
        text = parser_service.parse_document(
            file_content=file_content,
            mime_type=document.mime_type,
            filename=document.name,
        )

        if not text.strip():
            raise ValueError("Document parsing resulted in empty text")

        # Step 3: Chunk text
        logger.info(f"Chunking text ({len(text)} characters)")
        chunks = chunker_service.chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks")

        # Step 4: Generate embeddings (dense + sparse)
        logger.info("Generating dense embeddings")
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = embedding_service.get_embeddings(chunk_texts)

        logger.info("Generating sparse embeddings")
        sparse_embeddings = embedding_service.get_sparse_embeddings(chunk_texts)

        # Step 5: Store in Qdrant
        logger.info(f"Storing {len(embeddings)} vectors (dense + sparse) in Qdrant")

        # Ensure collection exists
        collection_name = document.collection.name
        qdrant_service.create_collection(collection_name)

        # Prepare points for Qdrant (dense + sparse vectors)
        points = []
        for i, (chunk, embedding, sparse) in enumerate(zip(chunks, embeddings, sparse_embeddings)):
            point_id = str(uuid4())
            points.append(
                {
                    "id": point_id,
                    "vector": embedding,
                    "sparse_indices": sparse[0],
                    "sparse_values": sparse[1],
                    "payload": {
                        "document_id": document_id,
                        "document_name": document.name,
                        "collection_id": document.collection_id,
                        "chunk_text": chunk.content,
                        "chunk_position": chunk.position,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                    },
                }
            )

        # Upsert to Qdrant
        qdrant_service.upsert_vectors(collection_name, points)

        # Update document status
        document.status = "ready"
        document.chunk_count = len(chunks)
        document.error_message = None

        # Update collection document count
        document.collection.document_count = (
            db.query(Document)
            .filter(Document.collection_id == document.collection_id)
            .filter(Document.status == "ready")
            .count()
        )

        db.commit()
        logger.info(f"Successfully ingested document {document_id}")

    except Exception as e:
        logger.error(f"Ingestion failed for document {document_id}: {e}")
        document.status = "failed"
        document.error_message = str(e)
        db.commit()
        raise


def delete_document_vectors(document_id: str, collection_name: str) -> None:
    """Delete all vectors associated with a document.

    Args:
        document_id: ID of the document.
        collection_name: Name of the Qdrant collection.
    """
    if qdrant_service.collection_exists(collection_name):
        qdrant_service.delete_by_document_id(collection_name, document_id)
