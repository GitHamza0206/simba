from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from simba.chatbot.demo.nodes.generate_node import generate
from simba.chatbot.demo.nodes.grade_node import grade

# ===========================================
# Import nodes
from simba.chatbot.demo.nodes.retrieve_node import retrieve
from simba.chatbot.demo.state import State
from simba.core.langfuse_config import get_langfuse_callback_handler

# ===========================================

workflow = StateGraph(State)
# Initialize MemorySaver with the configuration directly
memory = MemorySaver()

# ===========================================
# Define the nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade)
workflow.add_node("generate", generate)

# ===========================================

# ===========================================
# define the edges
workflow.add_edge(START, "retrieve")
# workflow.add_edge("retrieve", "grade")
# workflow.add_edge("grade", "generate")
workflow.add_edge("retrieve", "generate")
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


# Get Langfuse callback handler
langfuse_handler = get_langfuse_callback_handler()

# Compile the graph with the Langfuse callback handler configuration
graph = workflow.compile(checkpointer=memory).with_config({"callbacks": [langfuse_handler]})

if __name__ == "__main__":
    # Just invoke the graph directly - the callbacks are already configured
    print(graph.invoke({"messages": "what is insurance?"}))
    show_graph(graph)
