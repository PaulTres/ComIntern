from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from comintern.models.chat import MessageRole
from comintern.schemas.base import Base, enum_column, utcnow


class Message(Base):
    """One question or answer of a conversation."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[MessageRole] = mapped_column(enum_column(MessageRole, "message_role"))
    content: Mapped[str] = mapped_column(Text)
    # The agent that wrote an answer, e.g. knowledge_agent; empty for the user's messages.
    agent: Mapped[str | None] = mapped_column(String(64), default=None)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
