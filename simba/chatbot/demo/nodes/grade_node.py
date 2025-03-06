from simba.chatbot.demo.chains.grade_chain import grade_chain


def grade(state):
    """
    Grade answer for hallucination

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, score, that contains LLM generation
    """
    print("---GRADE---")
    question = state["messages"][-1].content
    documents = state["documents"]

    docs_content = "\n\n".join(doc.page_content for doc in documents)
    
    # Grade (callbacks are handled at the graph level)
    score = grade_chain.invoke(
        {
            "context": docs_content,
            "question": question,
        }
    )

    if score:
        print(f"GRADE: {score}")
        return {"documents": documents, "question": question, "score": score}
    else:
        return {"documents": documents, "question": question, "score": "0"}
