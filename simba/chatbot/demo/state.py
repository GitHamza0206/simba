from typing import Annotated, List, Sequence, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of retrieved documents
        reranked_documents: list of reranked documents
        compressed_documents: list of compressed documents for LLM context
        messages: list of messages
        transform_attempts: counter tracking query reformulation attempts
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    documents: List[dict]
    hyde_retreived: List[dict]
    reranked_documents: List[dict]
    compressed_documents: List[dict]
    question: str
    generation: str
    transform_attempts: Optional[int]
    sub_queries: List[str]
    summaries: List[str] 
    # New: Client-facing state representation


def for_client(state: State) -> dict:
    if "documents" in state.keys():
        return {
            "sources": [
                {
                    "file_name": doc.metadata.get("source"),
                }
                for doc in state["documents"]
            ]
        }
    else:
        return {}
