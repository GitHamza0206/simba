# simba/tests/test_parsing_tasks_sync.py

import uuid
from datetime import datetime
import pytest
from langchain.schema import Document
from simba.models.simbadoc import MetadataType, SimbaDoc

# This dummy database stub will be used for the test.
class DummyDB:
    def __init__(self, doc):
        self.doc = doc
        self.updated_document = None

    def get_document(self, document_id: str):
        # Return our dummy document regardless of the passed ID.
        return self.doc

    def update_document(self, document_id: str, simbadoc: SimbaDoc):
        # Record the document update.
        self.updated_document = simbadoc

    def close(self):
        pass

# A dummy load method that simulates returning parsed content.
def dummy_load(self):
    dummy_parsed_doc = Document(
        page_content="dummy parsed content",
        metadata={"source": "dummy"}
    )
    return [dummy_parsed_doc]

def test_parse_docling_task_sync(monkeypatch):
    # Create dummy metadata and a dummy SimbaDoc
    metadata = MetadataType(
        filename="dummy.pdf",
        file_path="/dummy/path/dummy.pdf",
        parsing_status="Unparsed",
        uploadedAt=datetime.now().isoformat()
    )
    dummy_doc = SimbaDoc(
        id=str(uuid.uuid4()),
        documents=[],
        metadata=metadata
    )

    # Create a dummy DB instance that returns our dummy document.
    dummy_db = DummyDB(dummy_doc)
    
    # Patch get_database() in the task module to return our dummy DB.
    monkeypatch.setattr("simba.tasks.parsing_tasks.get_database", lambda: dummy_db)
    
    # Patch the load() method of DoclingLoader to avoid real file access.
    from langchain_docling import DoclingLoader
    monkeypatch.setattr(DoclingLoader, "load", dummy_load)
    
    # Patch vector_store.add_documents so it does nothing.
    from simba.tasks.parsing_tasks import vector_store
    monkeypatch.setattr(vector_store, "add_documents", lambda docs: None)
    
    # Now import and run the parse_docling_task synchronously.
    from simba.tasks.parsing_tasks import parse_docling_task
    task_result = parse_docling_task.apply(args=[dummy_doc.id])
    result = task_result.get(timeout=10)
    
    # Verify that the task returned a success status with the proper document ID.
    assert result["status"] == "success"
    assert result["document_id"] == dummy_doc.id
    
    # Confirm that the dummy database registered an update with success status.
    updated_doc = dummy_db.updated_document
    assert updated_doc is not None
    assert updated_doc.metadata.parsing_status == "SUCCESS"
    assert updated_doc.metadata.parser == "docling"
    
    # Check that the dummy doc now contains the parsed document in its documents list.
    assert len(updated_doc.documents) == 1