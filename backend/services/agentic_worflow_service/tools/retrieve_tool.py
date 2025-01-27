from langchain_core.tools import tool
from services.vector_store_service import VectorStoreService
from core.config import Settings
# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@tool()
def retrieve(query: str):
    """Retrieve information related to a question from the knowledge base."""
    store = VectorStoreService()
    retrieved_docs = store.search(query, k=Settings.retrieval.k) 
    return format_docs(retrieved_docs)
