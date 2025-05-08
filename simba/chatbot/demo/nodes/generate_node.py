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
    
    # Use compressed documents as context (fallback to original documents if compression not available)
    context_docs = state["documents"]
    print(f"Using {len(context_docs)} compressed documents for generation")
    

    docs_content = "\n\n".join(
        doc.page_content
        for simbadoc in context_docs
        for doc in getattr(simbadoc, "documents", [])
    )

    summaries = state["summaries"]
    # RAG generation
    generation = generate_chain.invoke(
        {
            "summaries": summaries,
            "context": docs_content,
            "question": question,
            "chat_history": state["messages"],
        }
    )

    messages = state["messages"] + [AIMessage(content=generation)]

    # Return both the compressed documents and original documents to maintain state
    return {
        "documents": state.get("documents", []),
        "compressed_documents": context_docs,
        "messages": messages, 
        "generation": generation
    }
