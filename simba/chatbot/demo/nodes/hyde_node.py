from simba.chatbot.demo.chains.hyde_chain import hyde_chain
from simba.retrieval import Retriever
from simba.chatbot.demo.state import State
retriever = Retriever()

def hyde(state:State) -> State:
    """
    This node uses the hyde_chain to generate a hypothetical document that could answer the user's question.
    """
    question = state["messages"][-1].content

    hyde_document = hyde_chain.invoke({"question": question})
    hyde_retreived = retriever.retrieve(hyde_document, method="default")

    return {"hyde_retreived": hyde_retreived, "question": question}

