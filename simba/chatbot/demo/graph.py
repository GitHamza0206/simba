from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from simba.chatbot.demo.nodes.generate_node import generate
from simba.chatbot.demo.nodes.grade_node import grade
from simba.chatbot.demo.nodes.transform_query import transform_query
from simba.chatbot.demo.nodes.hallucination_node import grade_generation_v_documents_and_question
# ===========================================
# Import nodes
from simba.chatbot.demo.nodes.retrieve_node import retrieve
from simba.chatbot.demo.nodes.rerank_node import rerank
from simba.chatbot.demo.nodes.compress_node import compress
from simba.chatbot.demo.state import State

# ===========================================

workflow = StateGraph(State)
# Initialize MemorySaver with the configuration directly
memory = MemorySaver()

# ===========================================
# Define the nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("rerank", rerank)
workflow.add_node("compress", compress)
workflow.add_node("grade", grade)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)

# ===========================================
#EDGE functions 

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.
    Limits query transformation to a maximum of 2 attempts to prevent infinite loops.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    
    # Check if we've reached the maximum number of transformation attempts
    transform_attempts = state.get("transform_attempts", 0)
    MAX_TRANSFORM_ATTEMPTS = 2  # Limit to 2 attempts maximum
    
    if transform_attempts >= MAX_TRANSFORM_ATTEMPTS:
        print(f"Reached maximum query transformation attempts ({MAX_TRANSFORM_ATTEMPTS})")
        print("Proceeding to generate with best available information")
        return "generate"  # Force generation even with poor documents
    
    # Continue with normal assessment
    state["question"]
    # Use compressed documents for relevance assessment
    filtered_documents = state["compressed_documents"]

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
workflow.add_edge("retrieve", "rerank")
workflow.add_edge("rerank", "compress")
workflow.add_edge("compress", "grade")

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
