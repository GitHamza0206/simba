from typing import Annotated, List, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
        messages: list of messages
    """

    messages: Annotated[Sequence[BaseMessage] , add_messages]
    documents: List[dict]

    # New: Client-facing state representation
def for_client(state:State) -> dict:
    if "documents" in state.keys(): 
        return {
            "sources": [{
                "file_name": doc.metadata.get("source"),
            } for doc in state["documents"]]
        }
    else:
        return {}
