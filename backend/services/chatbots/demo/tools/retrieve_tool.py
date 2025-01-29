from langchain_core.tools import tool
from core.factories.vector_store_factory import VectorStoreFactory
from core.config import settings

store = VectorStoreFactory.get_vector_store()

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@tool()
def retrieve(query: str):
    """Retrieve information related to a question from the knowledge base."""

    retrieved_docs = store.search(query, k=settings.retrieval.k)
    return format_docs(retrieved_docs)
