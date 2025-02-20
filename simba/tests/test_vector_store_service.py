import os
import shutil
import uuid
from unittest.mock import Mock, patch

import pytest
from core.config import settings
from core.factories.vector_store_factory import VectorStoreFactory
from langchain.schema import Document


@pytest.fixture(autouse=True)
def clean_vector_store():
    """Clean up the vector store before and after each test"""
    # Clean before test
    if os.path.exists(settings.paths.faiss_index_dir):
        shutil.rmtree(settings.paths.faiss_index_dir)
    
    yield
    
    # Clean after test
    if os.path.exists(settings.paths.faiss_index_dir):
        shutil.rmtree(settings.paths.faiss_index_dir)

@pytest.fixture
def vector_store():
    return VectorStoreFactory.get_vector_store()

def test_delete_documents_success(vector_store):
    """Test successful document deletion"""
    # Setup
    doc_id1 = str(uuid.uuid4())
    doc_id2 = str(uuid.uuid4())
    test_docs = [
        Document(id=doc_id1, page_content="test1", metadata={}),
        Document(id=doc_id2, page_content="test2", metadata={})
    ]
    vector_store.add_documents(test_docs)
    
    # Execute
    result = vector_store.delete_documents([doc_id1, doc_id2])
    
    # Assert
    assert result is True
    assert vector_store.count_documents() == 0
    assert all(not vector_store.chunk_in_store(uid) for uid in [doc_id1, doc_id2])

def test_delete_documents_empty_list(vector_store):
    """Test deletion with empty list"""
    result = vector_store.delete_documents([])
    assert result is True

def test_delete_documents_nonexistent(vector_store):
    """Test deletion of nonexistent documents"""
    result = vector_store.delete_documents(["nonexistent_id"])
    assert result is True  # Should succeed even if documents don't exist

def test_delete_documents_verify_sync(vector_store):
    """Test store remains in sync after deletion"""
    # Setup
    doc_id = str(uuid.uuid4())
    test_doc = Document(id=doc_id, page_content="test", metadata={})
    vector_store.add_documents([test_doc])
    
    # Execute
    result = vector_store.delete_documents([doc_id])
    
    # Assert
    assert result is True
    assert vector_store.verify_store_sync()

def test_delete_documents_partial(vector_store):
    """Test deleting some documents while keeping others"""
    # Setup
    doc_id1 = str(uuid.uuid4())
    doc_id2 = str(uuid.uuid4())
    doc_id3 = str(uuid.uuid4())
    test_docs = [
        Document(id=doc_id1, page_content="test1", metadata={}),
        Document(id=doc_id2, page_content="test2", metadata={}),
        Document(id=doc_id3, page_content="test3", metadata={})
    ]
    vector_store.add_documents(test_docs)
    
    # Execute
    result = vector_store.delete_documents([doc_id1, doc_id2])
    
    # Assert
    assert result is True
    assert vector_store.count_documents() == 1
    assert not vector_store.chunk_in_store(doc_id1)
    assert not vector_store.chunk_in_store(doc_id2)
    assert vector_store.chunk_in_store(doc_id3) 