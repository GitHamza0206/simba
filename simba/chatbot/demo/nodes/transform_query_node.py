from simba.chatbot.demo.chains.transform_query_chain import question_rewrite_chain

def transform_query(state):
    """
    Transform the query to produce a better question.
    Tracks number of attempts to prevent infinite loops.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """ 

    print("---TRANSFORM QUERY---")
    question = state["messages"][-1].content
    
    # Track transformation attempts
    transform_attempts = state.get("transform_attempts", 0)
    transform_attempts += 1
    
    print(f"Query transformation attempt #{transform_attempts}")
    
    # Re-write question
    better_question = question_rewrite_chain.invoke({"question": question})
    
    return {
        "question": question,
        "sub_queries": better_question.sub_queries,
        "transform_attempts": transform_attempts
    }