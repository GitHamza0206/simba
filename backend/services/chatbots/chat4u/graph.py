import io
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from services.agentic_worflow_service.state import State
from langgraph.prebuilt import ToolNode, tools_condition
from services.agentic_worflow_service.tools.retrieve_tool import retrieve

#===========================================
# Import nodes
from services.agentic_worflow_service.nodes.assistant_node import assistant
from services.agentic_worflow_service.nodes.generate_node import generate
#===========================================

workflow = StateGraph(State)
# Initialize MemorySaver with the configuration directly
memory = MemorySaver()   

#===========================================
# Define the nodes
workflow.add_node("assistant", assistant)
retrieve_node = ToolNode([retrieve])
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate)

#===========================================

#===========================================
#define the edges
workflow.add_edge(START, "assistant")
workflow.add_conditional_edges(
    "assistant",
    tools_condition,
    {
        "tools":"retrieve",
        END: END,
    },

)


workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)


#===========================================


def save_graph(workflow):
    from PIL import Image
    import io
    import matplotlib.pyplot as plt
    #Generate and display the graph as an image
    image_bytes = workflow.get_graph().draw_mermaid_png()
    image = Image.open(io.BytesIO(image_bytes))

    plt.imshow(image)
    plt.axis('off')
    plt.show()  

# Compile
graph = workflow.compile()

if __name__ == "__main__":

    print(graph.invoke({"messages": "what is insurance?"}))
    save_graph(graph)
