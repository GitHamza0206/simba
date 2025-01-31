from typing import List, Annotated, Sequence
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
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
    documents: List[str]