from services.vector_store_service import VectorStoreService

store = VectorStoreService()
retriever = store.as_retriever()

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
   
    print("---RETRIEVE---")
    question = state["question"]
    # Retrieval
    documents = retriever.get_relevant_documents(question)
    print(f"Retrieved {len(documents)} documents")

    return {"documents": documents, "question": question}