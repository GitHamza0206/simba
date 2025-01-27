from services.chatbots.demo.chains.generate_chain import generate_chain
import time

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
    
    try:
        # Run with timeout
        response = generate_chain.invoke(
            {"context": docs, "question": question},
            config={"timeout": 60}  # 60 seconds timeout
        )
        return {"messages": [response]}
    
    except Exception as e:
        print(f"Unexpected error occurred: {str(e)}")
        return {"messages": [{"content": "I apologize, but I encountered an error while processing your request. Please try again."}]}