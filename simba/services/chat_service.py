"""Chat service with LangChain agent."""

import json
import logging
import time
from contextvars import ContextVar
from functools import lru_cache
from typing import AsyncGenerator

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from simba.core.config import settings
from simba.services import retrieval_service

logger = logging.getLogger(__name__)

# Context variable to store tool latencies
_tool_latencies: ContextVar[dict] = ContextVar("tool_latencies", default={})

# Global connection pool and checkpointer (async)
_connection_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None
_pool_initialized: bool = False

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


def create_rag_tool(collection_name: str):
    """Create a RAG tool bound to a specific collection."""

    @tool
    def rag(query: str) -> str:
        """Search the knowledge base for relevant information.

        Args:
            query: The search query to find relevant documents.

        Returns:
            Retrieved context from the knowledge base.
        """
        output, latency = retrieval_service.retrieve_formatted(
            query=query,
            collection_name=collection_name,
            limit=5,
            return_latency=True,
        )
        # Store latency in context var for SSE emission
        _tool_latencies.set({"rag": latency})
        return output

    return rag


def _get_reasoning_kwargs() -> dict:
    """Build reasoning kwargs based on provider and settings."""
    if not settings.llm_reasoning_effort:
        return {}

    # Parse provider from model string (e.g., "openai:gpt-4o" -> "openai")
    model = settings.llm_model
    provider = model.split(":")[0] if ":" in model else None

    # OpenAI (o1, o3, gpt-5) - uses reasoning_effort
    if provider == "openai":
        return {"reasoning_effort": settings.llm_reasoning_effort}

    # Anthropic (claude) - uses thinking with budget_tokens
    if provider == "anthropic":
        return {
            "thinking": {
                "type": "enabled",
                "budget_tokens": settings.llm_thinking_budget,
            }
        }

    # Ollama (local models like deepseek-r1) - uses reasoning
    if provider == "ollama":
        return {"reasoning": settings.llm_reasoning_effort}

    # xAI (grok) - uses extra_body
    if provider == "xai":
        return {"extra_body": {"reasoning_effort": settings.llm_reasoning_effort}}

    # Unknown provider - try generic reasoning_effort
    return {"reasoning_effort": settings.llm_reasoning_effort}


@lru_cache
def get_llm():
    """Get cached LLM instance with reasoning config."""
    reasoning_kwargs = _get_reasoning_kwargs()

    return init_chat_model(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        **reasoning_kwargs,
    )


async def get_checkpointer() -> AsyncPostgresSaver:
    """Get or create the async PostgreSQL checkpointer for conversation persistence."""
    global _connection_pool, _checkpointer, _pool_initialized

    if _checkpointer is None:
        logger.info("Initializing async PostgreSQL checkpointer for conversation persistence")

        # Run setup with autocommit=True (required for CREATE INDEX CONCURRENTLY)
        # This must be done with a separate sync connection
        with PostgresSaver.from_conn_string(settings.database_url) as setup_checkpointer:
            setup_checkpointer.setup()
        logger.info("PostgreSQL checkpointer tables created")

        # Create async connection pool
        _connection_pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            max_size=20,
            open=False,  # Don't open yet
        )
        _checkpointer = AsyncPostgresSaver(_connection_pool)
        logger.info("Async PostgreSQL checkpointer initialized successfully")

    # Ensure pool is open
    if not _pool_initialized and _connection_pool is not None:
        await _connection_pool.open()
        _pool_initialized = True

    return _checkpointer


async def shutdown_checkpointer() -> None:
    """Shutdown the checkpointer and close connections."""
    global _connection_pool, _checkpointer, _pool_initialized

    if _connection_pool is not None:
        logger.info("Closing async PostgreSQL connection pool")
        await _connection_pool.close()
        _connection_pool = None
        _checkpointer = None
        _pool_initialized = False


async def get_agent(collection: str | None = None):
    """Create agent with the specified collection.

    Args:
        collection: Collection name for RAG searches. Defaults to "default".
    """
    collection_name = collection or "default"
    llm = get_llm()
    rag_tool = create_rag_tool(collection_name)
    checkpointer = await get_checkpointer()

    agent = create_agent(
        model=llm,
        tools=[rag_tool],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


async def chat(message: str, thread_id: str, collection: str | None = None) -> str:
    """Process a chat message and return the response.

    Args:
        message: The user's message.
        thread_id: Thread ID for conversation isolation.
        collection: Collection name for RAG searches.

    Returns:
        The agent's response.
    """
    agent = await get_agent(collection)

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


async def chat_stream(
    message: str, thread_id: str, collection: str | None = None
) -> AsyncGenerator[str, None]:
    """Stream chat responses using SSE format with all event types.

    Args:
        message: The user's message.
        thread_id: Thread ID for conversation isolation.
        collection: Collection name for RAG searches.

    Yields:
        SSE-formatted events including:
        - type: "thinking" - Model thinking/reasoning content
        - type: "tool_start" - Tool invocation started (name, input)
        - type: "tool_end" - Tool finished (name, output/sources)
        - type: "content" - AI response text chunks
        - type: "done" - Stream complete (includes response latency)
    """
    agent = await get_agent(collection)
    config = {"configurable": {"thread_id": thread_id}}

    # Track tool start times for latency calculation
    tool_start_times: dict[str, float] = {}

    # Track response timing
    stream_start_time = time.perf_counter()
    first_token_time: float | None = None  # First content or thinking token
    tool_end_time: float | None = None  # When RAG tool finished

    # Track token counts
    reasoning_tokens = 0
    output_tokens = 0
    input_tokens = 0

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v2",
        ):
            event_type = event.get("event")
            event_data = event.get("data", {})

            # Tool invocation started
            if event_type == "on_tool_start":
                tool_name = event.get("name")
                tool_start_times[tool_name] = time.perf_counter()
                data = {
                    "type": "tool_start",
                    "name": tool_name,
                    "input": event_data.get("input"),
                }
                yield f"data: {json.dumps(data)}\n\n"

            # Tool finished - includes RAG sources
            elif event_type == "on_tool_end":
                # Extract output - may be a ToolMessage object or string
                output = event_data.get("output")
                if hasattr(output, "content"):
                    output = output.content
                elif not isinstance(output, (str, type(None))):
                    output = str(output)

                tool_name = event.get("name")

                # Get detailed latency from context var (set by rag tool)
                latencies = _tool_latencies.get()
                latency = latencies.get(tool_name, {}) if latencies else {}

                # If no detailed latency, calculate total from start time
                if not latency and tool_name in tool_start_times:
                    elapsed = (time.perf_counter() - tool_start_times[tool_name]) * 1000
                    latency = {"total_ms": elapsed}

                # Record when tool finished for response timing
                tool_end_time = time.perf_counter()

                data = {
                    "type": "tool_end",
                    "name": tool_name,
                    "output": output,
                    "latency": latency,
                }
                yield f"data: {json.dumps(data)}\n\n"

            # Chat model streaming chunks
            elif event_type == "on_chat_model_stream":
                chunk = event_data.get("chunk")
                if chunk:
                    content = chunk.content

                    # Extract token usage from chunk metadata if available
                    # OpenAI sends usage in the final streaming chunk
                    usage_metadata = getattr(chunk, "usage_metadata", None)
                    if usage_metadata:
                        input_tokens = usage_metadata.get("input_tokens", 0) or input_tokens
                        output_tokens = usage_metadata.get("output_tokens", 0) or output_tokens
                        # reasoning tokens in output_token_details.reasoning (OpenAI o1/o3 models)
                        output_details = usage_metadata.get("output_token_details") or {}
                        if output_details.get("reasoning"):
                            reasoning_tokens = output_details["reasoning"]

                    # Handle content as list (for thinking blocks, etc.)
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict):
                                block_type = block.get("type")
                                if block_type == "thinking":
                                    if first_token_time is None:
                                        first_token_time = time.perf_counter()
                                    thinking_content = block.get("thinking", "")
                                    data = {
                                        "type": "thinking",
                                        "content": thinking_content,
                                    }
                                    yield f"data: {json.dumps(data)}\n\n"
                                elif block_type == "text":
                                    text = block.get("text", "")
                                    if text:
                                        if first_token_time is None:
                                            first_token_time = time.perf_counter()
                                        data = {"type": "content", "content": text}
                                        yield f"data: {json.dumps(data)}\n\n"
                            elif isinstance(block, str) and block:
                                if first_token_time is None:
                                    first_token_time = time.perf_counter()
                                data = {"type": "content", "content": block}
                                yield f"data: {json.dumps(data)}\n\n"

                    # Handle content as string
                    elif isinstance(content, str) and content:
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        data = {"type": "content", "content": content}
                        yield f"data: {json.dumps(data)}\n\n"

                    # Handle tool call chunks (model deciding to call a tool)
                    tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
                    if tool_call_chunks:
                        for tool_chunk in tool_call_chunks:
                            data = {
                                "type": "tool_call",
                                "id": tool_chunk.get("id"),
                                "name": tool_chunk.get("name"),
                                "args": tool_chunk.get("args"),
                            }
                            yield f"data: {json.dumps(data)}\n\n"

            # Chat model end - get final usage metadata
            elif event_type == "on_chat_model_end":
                output = event_data.get("output")
                if output:
                    # Try to get usage metadata from the final output
                    usage_metadata = getattr(output, "usage_metadata", None)
                    if usage_metadata:
                        input_tokens = usage_metadata.get("input_tokens", 0) or input_tokens
                        output_tokens = usage_metadata.get("output_tokens", 0) or output_tokens
                        # reasoning tokens in output_token_details.reasoning (OpenAI o1/o3 models)
                        output_details = usage_metadata.get("output_token_details") or {}
                        if output_details.get("reasoning"):
                            reasoning_tokens = output_details["reasoning"]

        # Calculate response latency breakdown
        stream_end_time = time.perf_counter()
        response_latency = {}

        # Time to first token (from stream start)
        if first_token_time is not None:
            response_latency["ttft_ms"] = (first_token_time - stream_start_time) * 1000

        # Generation time = from after RAG tool to end of stream (LLM generation)
        if tool_end_time is not None:
            response_latency["generation_ms"] = (stream_end_time - tool_end_time) * 1000
        elif first_token_time is not None:
            # No tool call, generation is from first token to end
            response_latency["generation_ms"] = (stream_end_time - first_token_time) * 1000

        # Total response time
        response_latency["total_ms"] = (stream_end_time - stream_start_time) * 1000

        # Token counts
        if input_tokens > 0:
            response_latency["input_tokens"] = input_tokens
        if output_tokens > 0:
            response_latency["output_tokens"] = output_tokens
        if reasoning_tokens > 0:
            response_latency["reasoning_tokens"] = reasoning_tokens

        done_data = {"type": "done"}
        if response_latency:
            done_data["response_latency"] = response_latency
        yield f"data: {json.dumps(done_data)}\n\n"

    except Exception as e:
        # Log the full exception for debugging
        logger.exception(f"Chat stream error: {type(e).__name__}: {e}")
        # Send error event and done
        error_msg = str(e) if str(e) else f"{type(e).__name__}: Check server logs for details"
        error_data = {"type": "error", "message": error_msg}
        yield f"data: {json.dumps(error_data)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


# --- Conversation Management Functions ---


async def list_conversations(limit: int = 50, offset: int = 0) -> list[dict]:
    """List all conversations from the checkpoint store.

    Args:
        limit: Maximum number of conversations to return.
        offset: Number of conversations to skip.

    Returns:
        List of conversation metadata dictionaries.
    """
    # Ensure checkpointer is initialized (creates connection pool)
    await get_checkpointer()

    # Query unique thread_ids from checkpoints
    conversations = []

    try:
        async with _connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                # Get unique thread_ids with their latest checkpoint timestamp
                await cur.execute("""
                    SELECT DISTINCT ON (thread_id)
                        thread_id,
                        checkpoint_id,
                        thread_ts
                    FROM checkpoints
                    ORDER BY thread_id, thread_ts DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))

                rows = await cur.fetchall()

                for row in rows:
                    thread_id, checkpoint_id, thread_ts = row
                    conversations.append({
                        "id": thread_id,
                        "checkpoint_id": checkpoint_id,
                        "updated_at": thread_ts,
                    })

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")

    return conversations


async def get_conversation_messages(thread_id: str) -> list[dict]:
    """Get all messages for a conversation.

    Args:
        thread_id: The conversation thread ID.

    Returns:
        List of message dictionaries with role, content, and timestamp.
    """
    checkpointer = await get_checkpointer()

    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Get the latest checkpoint for this thread (async)
        checkpoint_tuple = await checkpointer.aget_tuple(config)

        if checkpoint_tuple is None:
            return []

        checkpoint = checkpoint_tuple.checkpoint
        messages_data = checkpoint.get("channel_values", {}).get("messages", [])

        messages = []
        for msg in messages_data:
            if isinstance(msg, HumanMessage):
                messages.append({
                    "role": "user",
                    "content": msg.content,
                    "id": msg.id if hasattr(msg, "id") else None,
                })
            elif isinstance(msg, AIMessage):
                # Skip tool call messages (they have empty content but tool_calls)
                if msg.content:
                    messages.append({
                        "role": "assistant",
                        "content": msg.content,
                        "id": msg.id if hasattr(msg, "id") else None,
                    })
            elif isinstance(msg, ToolMessage):
                # Include tool results as system messages for context
                messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_name": msg.name if hasattr(msg, "name") else "unknown",
                    "id": msg.id if hasattr(msg, "id") else None,
                })

        return messages

    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        return []


async def delete_conversation(thread_id: str) -> bool:
    """Delete a conversation and all its checkpoints.

    Args:
        thread_id: The conversation thread ID to delete.

    Returns:
        True if deleted successfully, False otherwise.
    """
    await get_checkpointer()

    try:
        async with _connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                # Delete all checkpoints for this thread
                await cur.execute(
                    "DELETE FROM checkpoints WHERE thread_id = %s",
                    (thread_id,)
                )
                # Also delete from checkpoint_writes if it exists
                await cur.execute(
                    "DELETE FROM checkpoint_writes WHERE thread_id = %s",
                    (thread_id,)
                )
                await conn.commit()
                return True
    except Exception as e:
        logger.error(f"Error deleting conversation {thread_id}: {e}")
        return False


async def get_conversation_count() -> int:
    """Get total number of unique conversations.

    Returns:
        Number of unique thread_ids in the checkpoint store.
    """
    await get_checkpointer()

    try:
        async with _connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
                result = await cur.fetchone()
                return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting conversations: {e}")
        return 0
