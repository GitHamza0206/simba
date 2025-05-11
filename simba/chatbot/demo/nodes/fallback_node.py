from simba.chatbot.demo.state import State

def fallback(state: State):
    return {"generation": "I'm sorry, I don't know how to answer that or you should give more information. Please try again."}