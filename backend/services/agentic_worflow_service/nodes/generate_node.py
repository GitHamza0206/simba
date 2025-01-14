
from services.agentic_worflow_service.chains.generate_chain import generate_chain

def generate(state):
    """
    Generate answer

    Args:
        state (messages): The current state

    Returns:
         dict: The updated state with re-phrased question
    """
    
    print("---GENERATE---")
    messages = state["messages"]
    question = messages[0].content
    last_message = messages[-1]

    docs = last_message.content
    # Run
    response = generate_chain.invoke({"context": docs, "question": question})
    
    return {"messages": [response]}