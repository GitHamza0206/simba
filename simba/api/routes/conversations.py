"""Conversation and chat routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from simba.services.chat_service import (
    chat as chat_service,
    chat_stream as chat_stream_service,
    delete_conversation as delete_conversation_service,
    get_conversation_count,
    get_conversation_message_count,
    get_conversation_messages as get_messages_service,
    list_conversations as list_conversations_service,
)

router = APIRouter(prefix="/conversations")


# --- Schemas ---


class MessageRequest(BaseModel):
    content: str
    conversation_id: str | None = None
    collection: str | None = None


class SourceReference(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str  # user, assistant
    content: str
    sources: list[SourceReference]
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int


# --- Routes ---


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all conversations with pagination."""
    conversations = await list_conversations_service(limit=limit, offset=offset)
    total = await get_conversation_count()

    items = []
    for conv in conversations:
        message_count = await get_conversation_message_count(conv["id"])
        items.append(
            ConversationResponse(
                id=conv["id"],
                created_at=conv.get("updated_at", datetime.utcnow()),
                updated_at=conv.get("updated_at", datetime.utcnow()),
                message_count=message_count,
            )
        )

    return ConversationListResponse(items=items, total=total)


@router.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """Send a message and get a response."""
    conversation_id = request.conversation_id or str(uuid4())

    response_content = await chat_service(
        message=request.content,
        thread_id=conversation_id,
        collection=request.collection,
    )

    return MessageResponse(
        id=str(uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=response_content,
        sources=[],  # TODO: Extract sources from RAG tool calls
        created_at=datetime.utcnow(),
    )


@router.post("/chat/stream")
async def chat_stream(request: MessageRequest):
    """Send a message and get a streaming SSE response."""
    conversation_id = request.conversation_id or str(uuid4())

    return StreamingResponse(
        chat_stream_service(
            message=request.content,
            thread_id=conversation_id,
            collection=request.collection,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-Conversation-Id": conversation_id,
        },
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get conversation details."""
    messages = await get_messages_service(conversation_id)

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        id=conversation_id,
        created_at=datetime.utcnow(),  # Could be improved with actual timestamp
        updated_at=datetime.utcnow(),
        message_count=len(messages),
    )


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation."""
    messages = await get_messages_service(conversation_id)

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Return messages in a simpler format (not MessageResponse which has sources)
    return [
        {
            "id": msg.get("id") or str(uuid4()),
            "conversation_id": conversation_id,
            "role": msg["role"],
            "content": msg["content"],
            "tool_name": msg.get("tool_name"),
        }
        for msg in messages
    ]


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    success = await delete_conversation_service(conversation_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

    return {"deleted": True, "id": conversation_id}
