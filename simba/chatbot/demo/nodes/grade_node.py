from simba.chatbot.demo.chains.grade_chain import grade_chain


def grade(state):
    """
    Grade compressed documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, grade, that contains grade
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["messages"][-1].content
    documents = state["compressed_documents"]

    # Score each doc
    filtered_docs = []
    for i,d in enumerate(documents):
        score = grade_chain.invoke({"question": question, "document": d.page_content})
        grade = score.binary_score
        if grade == "yes":
            print(f"---GRADE: DOCUMENT {i} RELEVANT---")
            filtered_docs.append(d)
        else:
            print(f"---GRADE: DOCUMENT {i} NOT RELEVANT---")
            continue

    return {"compressed_documents": filtered_docs, "question": question}
