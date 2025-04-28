from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from simba.chatbot.demo.nodes.generate_node import generate
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
workflow.add_node("generate", generate)

# ===========================================
#EDGE functions 

def decide_to_generate(state):
    """
    Determines whether to generate an answer based on document relevance.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    print("---ASSESS GRADED DOCUMENTS---")
    
    # Use compressed documents for relevance assessment
    filtered_documents = state["compressed_documents"]

    if not filtered_documents:
        # If no relevant documents, still try to generate with what we have
        print("---DECISION: NO RELEVANT DOCUMENTS, BUT PROCEEDING WITH GENERATION---")
        return "generate"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE WITH RELEVANT DOCUMENTS---")
        return "generate"

# ===========================================
# define the edges
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "rerank")
workflow.add_edge("rerank", "compress")
workflow.add_edge("compress", "generate")
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
