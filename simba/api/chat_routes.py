import json

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from simba.chatbot.demo.graph import graph
from simba.chatbot.demo.state import State, for_client

chat = APIRouter(prefix="/chat", tags=["chat"])    

# request input format
class Query(BaseModel):
    message: str


@chat.post("/")
async def invoke_graph(query: Query = Body(...)):
    """Invoke the graph workflow with a message"""

    
    config = {"configurable": {"thread_id": "2"}}
    state = State()
    state["messages"] = [HumanMessage(content=query.message)]


    # Helper function to check if string is numeric (including . and ,)
    def is_numeric(s):
        import re
        return bool(re.match(r'^[\d ]+$', s.strip()))
    
    
    async def generate_response():
        try:
            buffer = ""
            last_state = None

            async for event in graph.astream_events(state, version="v2", config=config ):
                metadata = event.get("metadata", {})
                event_type = event.get("event")

                # Handle retriever node completion
                if event_type == "on_chain_end" and event["name"] == "retrieve":
                    # Store documents from node output
                    state["documents"] = event["data"]["output"]["documents"]
                    last_state = for_client(state)
                    yield f"{json.dumps({'state': last_state})}\n\n"
                if event_type == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    state_snapshot = for_client(state)
                    last_state = state_snapshot  # Keep track of latest state
                    
                    # Buffer numeric chunks logic
                    if is_numeric(chunk) or (buffer and chunk in [" ", ",", "."]):
                        buffer += chunk
                    else:
                        if buffer:
                            combined = buffer + chunk
                            yield f"{json.dumps({'content': combined, 'state': last_state})}\n\n"
                            buffer = ""
                        else:
                            yield f"{json.dumps({'content': chunk, 'state': last_state})}\n\n"

                # Send state updates even when no content chunk
                elif event_type == "on_chat_end":
                    # Send the latest state that now includes documents
                    yield f"{json.dumps({'state': last_state})}\n\n"

        except Exception as e:
            yield f"{json.dumps({'error': str(e)})}\n\n"
        finally:
            print("Done")

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@chat.get("/status")
async def health():
    """Check the api is running"""
    return {"status": "🤙"}
    