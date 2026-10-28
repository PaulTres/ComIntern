"""Chat requests, stored messages and the names of the agents that answer."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AgentName(StrEnum):
    """The agents a turn can pass through."""

    ORCHESTRATOR_AGENT = "orchestrator_agent"
    KNOWLEDGE_AGENT = "knowledge_agent"
    REGULATION_AGENT = "regulation_agent"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Audience(StrEnum):
    """Who the answer is written for: the board's "different tones for different people"."""

    MANAGEMENT = "management"
    IT = "it"
    LEGAL = "legal"


class ChatStreamRequestModel(BaseModel):
    """One question sent to the assistant."""

    content: str = Field(
        min_length=1, max_length=4000, description="The user's question."
    )
    conversation_id: int | None = Field(
        default=None, description="Omit to start a new conversation."
    )
    regulation_code: str | None = Field(
        default=None, description="The regulation the user is looking at, if any."
    )
    audience: Audience | None = Field(
        default=None, description="Who the answer is written for."
    )


class SourceResponseModel(BaseModel):
    """A document an answer was written from."""

    title: str
    score: float


class ConversationResponseModel(BaseModel):
    """A conversation in the list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime


class MessageResponseModel(BaseModel):
    """A stored message of a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    agent: str | None
    sources: list[SourceResponseModel]
    created_at: datetime
