from typing import cast
from fastapi import APIRouter
from core.factories.database_factory import get_database
from models.simbadoc import SimbaDoc
from services.ingestion_service.document_ingestion_service import DocumentIngestionService

database_route   = APIRouter()

db = get_database()
kms = DocumentIngestionService()

@database_route.get("/database/info")
async def get_database_info():
    return db.__name__

@database_route.get("/database/documents")
async def get_database_documents():
    kms.sync_with_store()
    return db.get_all_documents()

@database_route.get("/database/langchain_documents")
async def get_langchain_documents():
    all_documents = db.get_all_documents()
    # to SimbaDoc
    simba_documents = [cast(SimbaDoc, doc) for doc in all_documents]
    # to Langchain documents
    langchain_documents = [simbadoc.documents for simbadoc in simba_documents]

    return langchain_documents

@database_route.delete("/database/clear_database")
async def clear_database():
    db.clear_database()
    return {"message": "Database cleared"}