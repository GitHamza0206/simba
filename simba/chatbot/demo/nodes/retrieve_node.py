from simba.retrieval import Retriever


retriever = Retriever()


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

        documents = retriever.retrieve(question, method="default")
        print(f"Retrieved {len(documents)} documents")

        return {"documents": documents, "question": question}
    except KeyError as e:
        print(f"Error retrieving documents: {e}")
        # Return empty documents list if retrieval fails
        return {"documents": [], "question": question}
