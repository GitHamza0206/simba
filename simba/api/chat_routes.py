import json
from typing import Dict, Any, Optional
import uuid

from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from simba.chatbot.demo.graph import graph
from simba.chatbot.demo.state import State, for_client
from simba.api.middleware.auth import get_current_user

chat = APIRouter(prefix="/chat", tags=["chat"])


# request input format
class Query(BaseModel):
    message: str
    session_id: Optional[str] = None


@chat.post("/")
async def invoke_graph(
    query: Query = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Invoke the graph workflow with a message"""

    user_id = current_user["id"]
    is_new_session = False
    session_id_for_graph: str

    if query.session_id:
        session_id_for_graph = query.session_id
    else:
        session_id_for_graph = str(uuid.uuid4())
        is_new_session = True

    config = {"configurable": {"thread_id": session_id_for_graph}}
    state = State()
    state["messages"] = [HumanMessage(content=query.message)]

    # Helper function to check if string is numeric (including . and ,)
    def is_numeric(s):
        import re

        return bool(re.match(r"^[\d ]+$", s.strip()))

    async def generate_response():
        try:
            buffer = ""
            last_state = None
            first_chunk_sent_for_new_session = False

            async for event in graph.astream_events(state, version="v2", config=config):
                event.get("metadata", {})
                event_type = event.get("event")

                response_payload = {}

                # Handle retriever node completion
                if event_type == "on_chain_end" and event["name"] == "retrieve":
                    # Store documents from node output
                    state["documents"] = event["data"]["output"]["documents"]
                    last_state = for_client(state)
                    response_payload['state'] = last_state
                    
                elif event_type == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    state_snapshot = for_client(state)
                    last_state = state_snapshot  # Keep track of latest state

                    # Buffer numeric chunks logic
                    if is_numeric(chunk) or (buffer and chunk in [" ", ",", "."]):
                        buffer += chunk
                    else:
                        if buffer:
                            response_payload['content'] = buffer + chunk
                            buffer = ""
                        else:
                            response_payload['content'] = chunk
                    response_payload['state'] = last_state
                
                elif event_type == "on_chat_end":
                    # Send the latest state that now includes documents if not already sent
                    if last_state:
                         response_payload['state'] = last_state

                # Send new_session_id with the first relevant chunk if it's a new session
                if is_new_session and not first_chunk_sent_for_new_session and ('content' in response_payload or 'state' in response_payload):
                    response_payload['new_session_id'] = session_id_for_graph
                    first_chunk_sent_for_new_session = True
                
                # Yield data if there's anything to send
                if response_payload:
                     yield f"{json.dumps(response_payload)}\n\n"
            
            # If there's any remaining buffer content after the loop (e.g. only numbers were sent at the end)
            if buffer: 
                final_payload = {'content': buffer, 'state': last_state}
                if is_new_session and not first_chunk_sent_for_new_session:
                    final_payload['new_session_id'] = session_id_for_graph
                yield f"{json.dumps(final_payload)}\n\n"

        except Exception as e:
            yield f"{json.dumps({'error': str(e)})}\n\n"
        finally:
            print("Done")

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@chat.get("/status")
async def health():
    """Check the api is running"""
    return {"status": "🤙"}
