from simba.retrieval import Retriever


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
        question = state["messages"][-1].content
        # Retrieval with error handling
        retriever = Retriever()
        ensemble_retriever = retriever.as_retriever()
        documents = ensemble_retriever.invoke(question)
        print(f"Retrieved {len(documents)} documents")
        
        return {"documents": documents, "question": question}
    except KeyError as e:
        print(f"Error retrieving documents: {e}")
        # Return empty documents list if retrieval fails
        return {"documents": [], "question": question}