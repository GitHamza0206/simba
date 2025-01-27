from services.chatbots.demo.chains.assistant_chain import assistant_chain

def assistant(state):

    """
    Invokes the agent model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the agent response appended to messages
    """
    print("---CALL AGENT---")
    messages = state["messages"]
    # Run
    response = assistant_chain.invoke(messages)
    
    return {"messages": [response]}