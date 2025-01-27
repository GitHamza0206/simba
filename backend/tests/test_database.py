from services.ingestion_service.document_ingestion_service import DocumentIngestionService
from core.factories.database_factory import get_database
from pprint import pprint

db = get_database()

def test_modify_document():
    doc = db.get_all_documents()[1]
    new_doc = doc.copy()
    new_doc.metadata.enabled = False
    db.update_document(doc.id, new_doc)
    pprint(doc.metadata)

if __name__ == "__main__":
    test_modify_document()