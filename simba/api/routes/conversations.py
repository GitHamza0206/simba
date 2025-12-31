"""Conversation and chat routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from simba.services.chat_service import chat as chat_service, get_agent

router = APIRouter(prefix="/conversations")


# --- Schemas ---


class MessageRequest(BaseModel):
    content: str
    conversation_id: str | None = None


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
async def list_conversations():
    """List all conversations."""
    # TODO: Implement actual conversation listing
    return ConversationListResponse(items=[], total=0)


@router.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """Send a message and get a response."""
    conversation_id = request.conversation_id or str(uuid4())

    response_content = await chat_service(
        message=request.content,
        thread_id=conversation_id,
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
    """Send a message and get a streaming response."""

    async def generate():
        # TODO: Implement actual streaming with LangChain
        words = "This is a placeholder streaming response. Chat functionality coming soon!".split()
        for word in words:
            yield f"data: {word} \n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get conversation details."""
    # TODO: Implement actual conversation retrieval
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation."""
    # TODO: Implement actual message retrieval
    return []


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    # TODO: Implement actual conversation deletion
    return {"deleted": True, "id": conversation_id}
