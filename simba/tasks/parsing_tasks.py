import logging

import torch

from simba.core.celery_config import celery_app as celery  # Rename for backward compatibility
from simba.core.factories.database_factory import get_database
from simba.embeddings import EmbeddingService
from simba.parsing.docling_parser import DoclingParser
from simba.parsing.mistral_ocr import MistralOCR

logger = logging.getLogger(__name__)


@celery.task(name="parse_docling")
def parse_docling_task(document_id: str):
    try:
        parser = DoclingParser()
        db = get_database()
        embedding_service = EmbeddingService()

        original_doc = db.get_document(document_id)

        parsed_simba_doc = parser.parse(original_doc)

        # Use EmbeddingService to handle embedding and storage
        embedding_service.embed_document(document_id)

        # Update database
        db.update_document(document_id, parsed_simba_doc)

        return {"status": "success", "document_id": parsed_simba_doc.id}
    except Exception as e:
        logger.error(f"Parse failed: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        if hasattr(db, "close"):
            db.close()
        # Clean up any remaining GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


@celery.task(name="mistral_ocr_task", bind=True)
def parse_mistral_ocr_task(self, document_id: str):
    """Parse a document using Mistral OCR"""
    logger.info(f"Starting Mistral OCR parsing for document: {document_id}")

    try:
        # Get document from database
        db = get_database()
        embedding_service = EmbeddingService()
        simbadoc = db.get_document(document_id)

        if not simbadoc:
            return {"status": "error", "error": "Document not found"}

        # Parse document
        parser = MistralOCR()
        parsed_simba_doc = parser.parse(simbadoc)

        # Process multimodal document using the embedding service
        embedding_service.process_multimodal_document(document_id)

        # Update database
        db.update_document(document_id, parsed_simba_doc)

        # Return success
        return {
            "status": "success",
            "document_id": document_id,
            "result": {
                "document_id": parsed_simba_doc.id,
                "num_chunks": len(parsed_simba_doc.documents) if parsed_simba_doc.documents else 0,
                "parsing_status": parsed_simba_doc.metadata.parsing_status,
                "parsed_at": (
                    (
                        parsed_simba_doc.metadata.parsed_at.isoformat()
                        if hasattr(parsed_simba_doc.metadata.parsed_at, "isoformat")
                        else parsed_simba_doc.metadata.parsed_at
                    )
                    if parsed_simba_doc.metadata.parsed_at
                    else None
                ),
            },
        }
    except Exception as e:
        logger.error(f"Mistral OCR parsing failed: {str(e)}", exc_info=True)
        return {"status": "error", "document_id": document_id, "error": str(e)}
    finally:
        # Clean up GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
