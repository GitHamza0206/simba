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
from simba.chatbot.demo.nodes.hyde_node import hyde
from simba.chatbot.demo.nodes.routing_node import routing
from simba.chatbot.demo.nodes.fallback_node import fallback
from simba.chatbot.demo.nodes.transform_query_node import transform_query
from simba.chatbot.demo.nodes.cot_node import cot
# ===========================================

workflow = StateGraph(State)
# Initialize MemorySaver with the configuration directly
memory = MemorySaver()

# ===========================================
# Define the nodes
# ===========================================
workflow.add_node("routing", routing)
workflow.add_node("fallback", fallback)
workflow.add_node("transform_query", transform_query)    
workflow.add_node("cot", cot)
workflow.add_node("retrieve", retrieve)
workflow.add_node("rerank", rerank)
workflow.add_node("compress", compress)
workflow.add_node("generate", generate)

# ===========================================
#EDGE functions 

# ===========================================
# define the edges
# workflow.add_conditional_edges(
#     START, 
#     routing # gives either "fallback" or "transform_query"
# )
workflow.add_edge(START, "transform_query")
workflow.add_edge("transform_query", "cot")
#workflow.add_edge("cot", "generate")
workflow.add_edge("cot", "retrieve")
workflow.add_edge("retrieve", "rerank")
workflow.add_edge("rerank", "generate")
#workflow.add_edge("compress", "generate")
workflow.add_edge("fallback", END)
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
