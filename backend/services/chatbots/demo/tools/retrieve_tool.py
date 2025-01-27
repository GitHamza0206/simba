from langchain_core.tools import tool
from services.vector_store_service import VectorStoreService
from core.config import settings

store = VectorStoreService()

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@tool()
def retrieve(query: str):
    """Retrieve information related to a question from the knowledge base."""

    retrieved_docs = store.search(query, k=settings.retrieval.k)
    return format_docs(retrieved_docs)
