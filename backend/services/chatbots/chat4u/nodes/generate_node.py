from ..chains.generate_chain import generate_chain
    
def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    generation = generate_chain.invoke({"context": documents, "question": question})
    return {"docume nts": documents, "question": question, "generation": generation}