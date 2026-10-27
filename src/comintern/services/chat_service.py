"""Prepare a chat turn, stream the orchestrator's answer, then save it."""

import logging
from collections.abc import AsyncGenerator
from itertools import pairwise

from comintern.agents.agent import HandOffEvent, RegulationReference
from comintern.agents.orchestrator.agent import OrchestratorAgent
from comintern.agents.orchestrator.context import OrchestratorContext
from comintern.database.session_factory import SessionFactory
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.chat import (
    ChatStreamRequestModel,
    ConversationResponseModel,
    MessageResponseModel,
    MessageRole,
)
from comintern.models.knowledge import ConversationTurn
from comintern.models.stream import (
    DeltaEventModel,
    ErrorEventModel,
    FinalEventModel,
    PayloadEventModel,
    StreamEventModel,
)
from comintern.repositories.conversation_repository import ConversationRepository
from comintern.repositories.regulation_repository import RegulationRepository
from comintern.schemas import Conversation, Message, User

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 80
HISTORY_TURNS = 3


class ChatService:
    """Chat turns and the conversations they are saved in."""

    def __init__(
        self, session_factory: SessionFactory, orchestrator: OrchestratorAgent
    ) -> None:
        self._session_factory = session_factory
        self._orchestrator = orchestrator

    async def prepare_turn(
        self, user: User, request: ChatStreamRequestModel
    ) -> AsyncGenerator[StreamEventModel]:
        """
        Check the conversation is the user's, save the question, and return the stream.

        These checks run before the response starts, so a wrong conversation is a plain 404.

        :raises AppError: CONVERSATION_NOT_FOUND when the conversation is another user's or gone.
        """
        async with self._session_factory.get_session() as session:
            conversations = ConversationRepository(session)
            if request.conversation_id is None:
                conversation = Conversation(
                    company_id=user.company_id,
                    user_id=user.id,
                    title=" ".join(request.content.split())[:MAX_TITLE_LENGTH],
                )
                await conversations.add(conversation)
                history: list[ConversationTurn] = []
            else:
                conversation = await conversations.get_owned(
                    user.id, request.conversation_id
                )
                if conversation is None:
                    raise AppError(AppErrorCode.CONVERSATION_NOT_FOUND)
                history = self._build_history(
                    await conversations.list_messages(conversation.id)
                )
            await conversations.add(
                Message(
                    conversation_id=conversation.id,
                    role=MessageRole.USER,
                    content=request.content,
                )
            )
            applicable_regulations = tuple(
                RegulationReference(
                    code=row.regulation.code, short_name=row.regulation.short_name
                )
                for row in await RegulationRepository(session).list_applicable(
                    user.company_id
                )
            )
        context = OrchestratorContext(
            company_id=user.company_id,
            company_name=user.company.name,
            applicable_regulations=applicable_regulations,
            conversation_id=conversation.id,
            question=request.content,
            regulation_code=request.regulation_code,
            audience=request.audience,
            history=tuple(history),
        )
        return self._stream_turn(context)

    async def list_conversations(self, user_id: int) -> list[ConversationResponseModel]:
        async with self._session_factory.get_session() as session:
            return [
                ConversationResponseModel.model_validate(conversation)
                for conversation in await ConversationRepository(session).list_for_user(
                    user_id
                )
            ]

    async def list_messages(
        self, user_id: int, conversation_id: int
    ) -> list[MessageResponseModel]:
        """
        :raises AppError: CONVERSATION_NOT_FOUND when the conversation is another user's or gone.
        """
        async with self._session_factory.get_session() as session:
            conversations = ConversationRepository(session)
            if await conversations.get_owned(user_id, conversation_id) is None:
                raise AppError(AppErrorCode.CONVERSATION_NOT_FOUND)
            return [
                MessageResponseModel.model_validate(message)
                for message in await conversations.list_messages(conversation_id)
            ]

    async def _stream_turn(
        self, context: OrchestratorContext
    ) -> AsyncGenerator[StreamEventModel]:
        """
        Stream the orchestrator's events, save the answer, then send final; a failure after
        the stream started is sent as an error event.
        """
        answer, sources, agents = "", [], []
        try:
            async for event in self._orchestrator.astream(context):
                match event:
                    case HandOffEvent(agent=agent):
                        agents.append(agent.value)
                        continue
                    case DeltaEventModel(text=text):
                        answer += text
                    case PayloadEventModel(value=value):
                        sources = [source.model_dump() for source in value]
                yield event
            async with self._session_factory.get_session() as session:
                message = Message(
                    conversation_id=context.conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=answer,
                    agent=",".join(agents) or None,
                    sources=sources,
                )
                await ConversationRepository(session).add(message)
            yield FinalEventModel(
                conversation_id=context.conversation_id, message_id=message.id
            )
        except Exception as error:
            logger.exception(
                "Chat turn failed in conversation_id=%s", context.conversation_id
            )
            error_code = (
                error.error
                if isinstance(error, AppError)
                else AppErrorCode.CHAT_STREAM_FAILED
            )
            yield ErrorEventModel(code=error_code.name, detail=error_code.value.message)

    @staticmethod
    def _build_history(messages: list[Message]) -> list[ConversationTurn]:
        """
        :return: The last answered turns, oldest first.
        """
        turns = [
            ConversationTurn(question=question.content, answer=answer.content)
            for question, answer in pairwise(messages)
            if question.role == MessageRole.USER
            and answer.role == MessageRole.ASSISTANT
        ]
        return turns[-HISTORY_TURNS:]
