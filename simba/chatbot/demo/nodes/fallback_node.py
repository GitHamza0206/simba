from simba.chatbot.demo.state import State
from langchain_core.messages import HumanMessage, AIMessage


def fallback(state: State):
    messages = state["messages"]
    messages.append(AIMessage(content="I'm sorry, I don't know how to answer that or you should give more information. Please try again."))      
    generation = AIMessage(content="I'm sorry, I don't know how to answer that or you should give more information. Please try again.")
    return {"messages": messages, "generation": generation}