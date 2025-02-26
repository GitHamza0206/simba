from langchain_core.messages import AIMessage

from simba.chatbot.demo.chains.generate_chain import generate_chain


def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["messages"][-1].content
    documents = state["documents"]

    docs_content = "\n\n".join(doc.page_content for doc in documents)
    # RAG generation
    generation = generate_chain.invoke(
        {
            "context": docs_content,
            "question": question,
            "chat_history": state["messages"],
        }
    )
    messages = state["messages"] + [AIMessage(content=generation)]

    return {"documents": documents, "messages": messages}
