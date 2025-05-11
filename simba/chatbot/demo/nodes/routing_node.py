from simba.chatbot.demo.chains.routing_chain import routing_chain
from simba.chatbot.demo.state import State

def routing(state: State):
    question = state["messages"][-1].content
    route = routing_chain.invoke({"question": question})
    return route.route