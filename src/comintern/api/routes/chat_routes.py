from collections.abc import AsyncGenerator

from fastapi import APIRouter
from fastapi.sse import EventSourceResponse, ServerSentEvent

from comintern.api.dependencies import (
    ChatServiceDependency,
    ChatStreamDependency,
    CurrentUserDependency,
)
from comintern.models.chat import ConversationResponseModel, MessageResponseModel

router = APIRouter(tags=["chat"])


@router.post("/chat/stream", response_class=EventSourceResponse, response_model=None)
async def stream_chat(stream: ChatStreamDependency) -> AsyncGenerator[ServerSentEvent]:
    """
    Ask the assistant. Omit conversation_id to start a conversation. The answer streams as
    server-sent events: progress, delta, payload (sources), then final, or error.
    """
    async for event in stream:
        yield ServerSentEvent(
            event=event.event_type.value,
            raw_data=event.model_dump_json(exclude_none=True),
        )


@router.get("/conversations", response_model=list[ConversationResponseModel])
async def list_conversations(
    user: CurrentUserDependency, chat_service: ChatServiceDependency
) -> list[ConversationResponseModel]:
    return await chat_service.list_conversations(user.id)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponseModel],
)
async def list_messages(
    conversation_id: int,
    user: CurrentUserDependency,
    chat_service: ChatServiceDependency,
) -> list[MessageResponseModel]:
    return await chat_service.list_messages(user.id, conversation_id)
