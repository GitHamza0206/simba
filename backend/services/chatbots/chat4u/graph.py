import io
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from .state import State


#===========================================
# Import nodes
from .nodes.retrieve_node import retrieve
from .nodes.grade_node import grade
from .nodes.generate_node import generate
#===========================================

workflow = StateGraph(State)
# Initialize MemorySaver with the configuration directly
memory = MemorySaver()   

#===========================================
# Define the nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade)
workflow.add_node("generate", generate)

#===========================================

#===========================================
#define the edges
workflow.add_edge(START, "retrieve")
#workflow.add_edge("retrieve", "grade")
#workflow.add_edge("grade", "generate")
workflow.add_edge("retrieve" , "generate")
workflow.add_edge("generate", END)


#===========================================


def show_graph(workflow):
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
graph = workflow.compile(checkpointer=memory)

if __name__ == "__main__":

    print(graph.invoke({"messages": "what is insurance?"}))
    show_graph(graph)