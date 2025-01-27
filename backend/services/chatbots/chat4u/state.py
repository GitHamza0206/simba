from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[Sequence[BaseMessage], add_messages]

