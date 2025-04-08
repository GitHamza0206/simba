from simba.chatbot.demo.chains.question_rewrite_chain import question_rewrite_chain

def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """ 

    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]

    # Re-write question
    better_question = question_rewrite_chain.invoke({"question": question})
    return {"documents": documents, "question": better_question}