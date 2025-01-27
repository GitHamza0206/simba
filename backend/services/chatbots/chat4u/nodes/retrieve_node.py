from services.vector_store_service import VectorStoreService

store = VectorStoreService()
retriever = store.as_retriever(
    search_kwargs={"k": 4}
)

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    try:
        print("---RETRIEVE---")
        question = state["question"]
        # Retrieval with error handling
        documents = retriever.invoke(question)
        print(f"Retrieved {len(documents)} documents")
        
        return {"documents": documents, "question": question}
    except KeyError as e:
        print(f"Error retrieving documents: {e}")
        # Return empty documents list if retrieval fails
        return {"documents": [], "question": question}