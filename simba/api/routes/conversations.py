"""Conversation and chat routes."""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from simba.api.middleware.auth import OrganizationContext, get_current_org
from simba.services.chat_service import (
    chat as chat_service,
)
from simba.services.chat_service import (
    chat_stream as chat_stream_service,
)
from simba.services.chat_service import (
    delete_conversation as delete_conversation_service,
)
from simba.services.chat_service import (
    get_conversation_message_count,
)
from simba.services.chat_service import (
    get_conversation_messages as get_messages_service,
)
from simba.services.chat_service import (
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


def get_org_prefixed_thread_id(org_id: str, conversation_id: str) -> str:
    """Generate org-namespaced thread ID for LangGraph checkpointer."""
    return f"{org_id}:{conversation_id}"


def extract_conversation_id(org_prefixed_id: str, org_id: str) -> str | None:
    """Extract conversation ID from org-prefixed thread ID."""
    prefix = f"{org_id}:"
    if org_prefixed_id.startswith(prefix):
        return org_prefixed_id[len(prefix) :]
    return None


# --- Routes ---


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    org: OrganizationContext = Depends(get_current_org),
):
    """List all conversations for the current organization with pagination."""
    # Get all conversations and filter by org prefix
    all_conversations = await list_conversations_service(limit=1000, offset=0)
    org_prefix = f"{org.organization_id}:"

    # Filter to only include conversations for this org
    org_conversations = [c for c in all_conversations if c["id"].startswith(org_prefix)]
    total = len(org_conversations)

    # Apply pagination
    paginated = org_conversations[offset : offset + limit]

    items = []
    for conv in paginated:
        message_count = await get_conversation_message_count(conv["id"])
        # Extract the actual conversation ID without org prefix
        actual_id = extract_conversation_id(conv["id"], org.organization_id)
        if actual_id:
            items.append(
                ConversationResponse(
                    id=actual_id,
                    created_at=conv.get("updated_at", datetime.utcnow()),
                    updated_at=conv.get("updated_at", datetime.utcnow()),
                    message_count=message_count,
                )
            )

    return ConversationListResponse(items=items, total=total)


@router.post("/chat", response_model=MessageResponse)
async def chat(
    request: MessageRequest,
    org: OrganizationContext = Depends(get_current_org),
):
    """Send a message and get a response."""
    conversation_id = request.conversation_id or str(uuid4())
    # Use org-prefixed thread ID for storage
    thread_id = get_org_prefixed_thread_id(org.organization_id, conversation_id)

    # Use org-namespaced collection name for RAG
    collection = None
    if request.collection:
        collection = f"{org.organization_id}_{request.collection}"

    response_content = await chat_service(
        message=request.content,
        thread_id=thread_id,
        collection=collection,
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
async def chat_stream(
    request: MessageRequest,
    org: OrganizationContext = Depends(get_current_org),
):
    """Send a message and get a streaming SSE response."""
    conversation_id = request.conversation_id or str(uuid4())
    # Use org-prefixed thread ID for storage
    thread_id = get_org_prefixed_thread_id(org.organization_id, conversation_id)

    # Use org-namespaced collection name for RAG
    collection = None
    if request.collection:
        collection = f"{org.organization_id}_{request.collection}"

    return StreamingResponse(
        chat_stream_service(
            message=request.content,
            thread_id=thread_id,
            collection=collection,
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
async def get_conversation(
    conversation_id: str,
    org: OrganizationContext = Depends(get_current_org),
):
    """Get conversation details."""
    thread_id = get_org_prefixed_thread_id(org.organization_id, conversation_id)
    messages = await get_messages_service(thread_id)

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        id=conversation_id,
        created_at=datetime.utcnow(),  # Could be improved with actual timestamp
        updated_at=datetime.utcnow(),
        message_count=len(messages),
    )


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    org: OrganizationContext = Depends(get_current_org),
):
    """Get all messages in a conversation."""
    thread_id = get_org_prefixed_thread_id(org.organization_id, conversation_id)
    messages = await get_messages_service(thread_id)

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
async def delete_conversation(
    conversation_id: str,
    org: OrganizationContext = Depends(get_current_org),
):
    """Delete a conversation and all its messages."""
    thread_id = get_org_prefixed_thread_id(org.organization_id, conversation_id)
    success = await delete_conversation_service(thread_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

    return {"deleted": True, "id": conversation_id}
