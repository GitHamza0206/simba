from services.ingestion_service.document_ingestion_service import (
    DocumentIngestionService,
)


def test_embedding_from_folder():
    ingestion_service = DocumentIngestionService()
    ingestion_service.ingest_markdowns_from_dir()


def test_document_loading_from_folder():
    ingestion_service = DocumentIngestionService()
    documents_dict = ingestion_service.get_ingested_documents_by_folder()
    print(documents_dict)


if __name__ == "__main__":
    test_embedding_from_folder()
