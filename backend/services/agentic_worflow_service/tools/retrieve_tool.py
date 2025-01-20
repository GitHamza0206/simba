from langchain_core.tools import tool
from services.vector_store_service import VectorStoreService

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@tool()
def retrieve(query: str):
    """Retrieve information related to a question from the knowledge base."""
    store = VectorStoreService()
    retrieved_docs = store.search(query, k=2) #TODO : change k to config
    return format_docs(retrieved_docs)
