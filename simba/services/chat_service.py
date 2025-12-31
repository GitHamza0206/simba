"""Chat service with LangChain agent."""

from functools import lru_cache

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from simba.core.config import settings
from simba.services import retrieval_service

SYSTEM_PROMPT = """You are Simba, a helpful customer service assistant.

Your role is to help users by:
1. Answering questions using information from the knowledge base (RAG)
2. Being friendly, professional, and concise
3. Admitting when you don't know something

When a user asks a question, use the rag tool to search for relevant information
before answering. Always base your answers on the retrieved context when available.

If the rag tool returns "No relevant information found", let the user know you
couldn't find specific information but offer to help in other ways.
"""


@tool
def rag(query: str, collection: str = "default") -> str:
    """Search the knowledge base for relevant information.

    Args:
        query: The search query to find relevant documents.
        collection: The collection name to search in. Default is "default".

    Returns:
        Retrieved context from the knowledge base.
    """
    return retrieval_service.retrieve_formatted(
        query=query,
        collection_name=collection,
        limit=5,
    )


@lru_cache
def get_agent():
    """Create and return the cached chat agent with checkpointer for conversation memory."""
    llm = init_chat_model(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )

    # MemorySaver for dev; use PostgresSaver for production
    checkpointer = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=[rag],
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


async def chat(message: str, thread_id: str) -> str:
    """Process a chat message and return the response.

    Args:
        message: The user's message.
        thread_id: Thread ID for conversation isolation.

    Returns:
        The agent's response.
    """
    agent = get_agent()

    config = {"configurable": {"thread_id": thread_id}}

    response = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    # Extract the last AI message
    ai_messages = [m for m in response["messages"] if m.type == "ai"]
    if ai_messages:
        return ai_messages[-1].content

    return "I apologize, but I couldn't generate a response."
