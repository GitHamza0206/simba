from pydantic import BaseModel

from simba.chatbot.demo.chains.grade_chain import grade_chain


def grade(state):
    """
    Grade documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, grade, that contains grade
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    # Score each doc
    filtered_docs = []
    for d in documents:
        score = grade_chain.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    
    return {"documents": filtered_docs, "question": question}