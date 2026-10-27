from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comintern.schemas import Conversation, Message


class ConversationRepository:
    """Conversations with the assistant and their messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_owned(
        self, user_id: int, conversation_id: int
    ) -> Conversation | None:
        """
        :return: The conversation, or None when it does not exist or another user started it.
        """
        conversation = await self._session.get(Conversation, conversation_id)
        return (
            conversation
            if conversation is not None and conversation.user_id == user_id
            else None
        )

    async def list_for_user(self, user_id: int) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        return list(await self._session.scalars(statement))

    async def list_messages(self, conversation_id: int) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id)
        )
        return list(await self._session.scalars(statement))

    async def add(self, row: Conversation | Message) -> None:
        self._session.add(row)
        await self._session.flush()
