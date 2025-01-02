
import json
from fastapi import APIRouter,Body
from services.classes.state_class import State
from services.flow_graph import graph
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

chat = APIRouter()    

# request input format
class Query(BaseModel):
    message: str


@chat.post("/chat")
async def invoke_graph(query: Query = Body(...)):
    """Invoke the graph workflow with a message"""

    
    config = {"configurable": {"thread_id": "2"}}
    state = State()
    state["messages"] = [("user", query.message)]
    state["question"] = query.message

    # Helper function to check if string is numeric (including . and ,)
    def is_numeric(s):
        import re
        return bool(re.match(r'^[\d ]+$', s.strip()))
    
    
    async def generate_response():
        try:
            # Initialize buffer for numeric chunks
            buffer = ""

            async for event in graph.astream_events(
                state,
                version="v2", 
                config=config,
                
            ):
                
                # Access the metadata field
                metadata = event.get("metadata", {})
                event_type = event.get("event")
                key=metadata.get("langgraph_node")

                # Only stream for specific nodes
                allowed_nodes = ["generate","transform_query"]
                if key not in allowed_nodes:
                    continue
                

                if event_type == "on_chat_model_start":      
                    yield json.dumps({
                        "status": "start",
                        "node": key,
                        "details": "Node stream started"
                    }) + "\n"
                    
                # Emit raw data for the streaming events
                elif event_type == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    
                   
                    # Buffer numeric chunks until we get non-numeric content
                    if is_numeric(chunk) or (buffer and chunk in [" ", ",", "."]):
                        buffer += chunk
                    else:
                        # Output buffered content if any, otherwise output current chunk
                        if buffer:
                            buffer += chunk
                            yield buffer
                            buffer = ""
                        else:
                            yield chunk
                        

                # Emit end of the node stream as a JSON object
                elif event_type == "on_chat_model_end":
                    yield json.dumps({
                        "status": "end",
                        "node": key,
                        "details": "Node stream ended"
                    }) + "\n"
                    
                
                # if event["event"] == "on_chat_model_stream":
                #     chunk = event["data"]["chunk"].content
                #     yield chunk
           
        except Exception as e:
            yield f"Error: {str(e)}"
        finally:
            print("Done")

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@chat.get("/status")
async def health():
    """Check the api is running"""
    return {"status": "🤙"}
    