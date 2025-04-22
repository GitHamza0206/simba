from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from simba.chatbot.demo.nodes.generate_node import generate
from simba.chatbot.demo.nodes.grade_node import grade
from simba.chatbot.demo.nodes.transform_query import transform_query
from simba.chatbot.demo.nodes.hallucination_node import grade_generation_v_documents_and_question
# ===========================================
# Import nodes
from simba.chatbot.demo.nodes.retrieve_node import retrieve
from simba.chatbot.demo.state import State

# ===========================================

workflow = StateGraph(State)
# Initialize MemorySaver with the configuration directly
memory = MemorySaver()

# ===========================================
# Define the nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)

# ===========================================
#EDGE functions 

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    state["question"]
    filtered_documents = state["documents"]

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print(
            "---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "generate"






# ===========================================
# define the edges
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade")

workflow.add_conditional_edges(
    "grade",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)

workflow.add_edge("transform_query", "retrieve")
workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "transform_query",
    },
)

workflow.add_edge("generate", END)


# ===========================================


def show_graph(workflow):
    import io

    import matplotlib.pyplot as plt
    from PIL import Image

    # Generate and display the graph as an image
    image_bytes = workflow.get_graph().draw_mermaid_png()
    image = Image.open(io.BytesIO(image_bytes))

    plt.imshow(image)
    plt.axis("off")
    plt.show()


# Compile
graph = workflow.compile(checkpointer=memory)

if __name__ == "__main__":

    print(graph.invoke({"messages": "qui est le patront de atlanta ?"}))
    #show_graph(graph)
