from fastapi import APIRouter
from core.factories.database_factory import get_database

database_route   = APIRouter()

db = get_database()

@database_route.get("/database/info")
async def get_database_info():
    return db.__name__

@database_route.get("/database/documents")
async def get_database_documents():
    return db.get_all_documents()