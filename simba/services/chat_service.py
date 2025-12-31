"""Chat service with LangChain agent."""

import json
from functools import lru_cache
from typing import AsyncGenerator

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

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

    agent = create_agent(
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


async def chat_stream(message: str, thread_id: str) -> AsyncGenerator[str, None]:
    """Stream chat responses using SSE format with all event types.

    Args:
        message: The user's message.
        thread_id: Thread ID for conversation isolation.

    Yields:
        SSE-formatted events including:
        - type: "thinking" - Model thinking/reasoning content
        - type: "tool_start" - Tool invocation started (name, input)
        - type: "tool_end" - Tool finished (name, output/sources)
        - type: "content" - AI response text chunks
        - type: "done" - Stream complete
    """
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=message)]},
        config=config,
        version="v2",
    ):
        event_type = event.get("event")
        event_data = event.get("data", {})

        # Tool invocation started
        if event_type == "on_tool_start":
            yield f"data: {json.dumps({
                'type': 'tool_start',
                'name': event.get('name'),
                'input': event_data.get('input'),
            })}\n\n"

        # Tool finished - includes RAG sources
        elif event_type == "on_tool_end":
            yield f"data: {json.dumps({
                'type': 'tool_end',
                'name': event.get('name'),
                'output': event_data.get('output'),
            })}\n\n"

        # Chat model streaming chunks
        elif event_type == "on_chat_model_stream":
            chunk = event_data.get("chunk")
            if chunk:
                content = chunk.content

                # Handle content as list (for thinking blocks, etc.)
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            block_type = block.get("type")
                            if block_type == "thinking":
                                yield f"data: {json.dumps({
                                    'type': 'thinking',
                                    'content': block.get('thinking', ''),
                                })}\n\n"
                            elif block_type == "text":
                                text = block.get("text", "")
                                if text:
                                    yield f"data: {json.dumps({
                                        'type': 'content',
                                        'content': text,
                                    })}\n\n"
                        elif isinstance(block, str) and block:
                            yield f"data: {json.dumps({
                                'type': 'content',
                                'content': block,
                            })}\n\n"

                # Handle content as string
                elif isinstance(content, str) and content:
                    yield f"data: {json.dumps({
                        'type': 'content',
                        'content': content,
                    })}\n\n"

                # Handle tool call chunks (model deciding to call a tool)
                tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
                if tool_call_chunks:
                    for tool_chunk in tool_call_chunks:
                        yield f"data: {json.dumps({
                            'type': 'tool_call',
                            'id': tool_chunk.get('id'),
                            'name': tool_chunk.get('name'),
                            'args': tool_chunk.get('args'),
                        })}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
