import logging
from collections.abc import AsyncIterator
from typing import Any

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Overwrite

from comintern.agents.agent import Agent, AgentEvent
from comintern.agents.knowledge_agent.answer_chain import (
    build_answer_chain,
    build_answer_input,
)
from comintern.agents.knowledge_agent.context import (
    KnowledgeAgentContext,
    KnowledgeRuntimeContext,
)
from comintern.agents.knowledge_agent.helpers import build_sources
from comintern.agents.knowledge_agent.middleware import TurnLimitMiddleware
from comintern.agents.knowledge_agent.prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    RETRIEVE_DOCUMENTS_TOOL,
)
from comintern.agents.knowledge_agent.state import KnowledgeAgentState
from comintern.agents.knowledge_agent.tools.retrieve_documents import retrieve_documents
from comintern.agents.tool_filter_middleware import ToolFilterMiddleware
from comintern.configuration.config import KnowledgeAgentSettings
from comintern.models.chat import AgentName
from comintern.models.knowledge import Chunk, ConversationTurn
from comintern.models.stream import (
    DeltaEventModel,
    PayloadEventModel,
    ProgressEventModel,
    ProgressStep,
)
from comintern.services.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class KnowledgeAgent(Agent[KnowledgeAgentContext]):
    """
    Answers questions about what the regulations say, from the catalog, the official texts and
    the company's own documents.

    A turn has two steps: a retrieval agent searches with a tool, then the answer chain writes
    the answer from the passages it found. Each conversation keeps its own thread, so a
    follow-up such as "and in Romania?" is searched in context.
    """

    name = AgentName.KNOWLEDGE_AGENT
    description = "Answers what a regulation says, from the official texts and the company's documents."

    def __init__(
        self,
        chat_model: BaseChatModel,
        knowledge_base: KnowledgeBase,
        settings: KnowledgeAgentSettings,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._knowledge_base = knowledge_base
        self._settings = settings
        self._answer_chain = build_answer_chain(chat_model)
        self._retrieval_graph: CompiledStateGraph = create_deep_agent(
            model=chat_model,
            tools=[retrieve_documents],
            system_prompt=RETRIEVAL_SYSTEM_PROMPT,
            state_schema=KnowledgeAgentState,
            context_schema=KnowledgeRuntimeContext,
            middleware=[
                ToolFilterMiddleware({RETRIEVE_DOCUMENTS_TOOL}),
                TurnLimitMiddleware(settings.history_turns),
            ],
            checkpointer=checkpointer,
            name=self.name.value,
        )

    async def astream(
        self, context: KnowledgeAgentContext
    ) -> AsyncIterator[AgentEvent]:
        """
        Search, then stream the answer; the sources follow when passages were found.

        :param context: The question, the company and the conversation.
        :return: Progress, the answer in pieces, then the sources.
        """
        config = self._build_config(context)
        history = await self._read_history(config)

        yield ProgressEventModel(step=ProgressStep.SEARCHING)
        chunks = await self._find_chunks(context, config)

        yield ProgressEventModel(step=ProgressStep.WRITING)
        answer = ""
        async for piece in self._answer_chain.astream(
            build_answer_input(context.question, history, chunks, context.audience)
        ):
            answer += piece
            yield DeltaEventModel(text=piece)

        await self._retrieval_graph.aupdate_state(
            config,
            {
                "history": [
                    *history,
                    ConversationTurn(question=context.question, answer=answer),
                ][-self._settings.history_turns :]
            },
        )
        if chunks:
            yield PayloadEventModel(value=build_sources(chunks))

    async def _find_chunks(
        self, context: KnowledgeAgentContext, config: RunnableConfig
    ) -> list[Chunk]:
        """
        Run the retrieval agent, keeping its state after every step, so the passages found
        before a failure or the recursion limit are still used.
        """
        last_state: dict[str, Any] = {}
        try:
            async for state in self._retrieval_graph.astream(
                {
                    "messages": [HumanMessage(content=context.question)],
                    "chunks": Overwrite([]),
                },
                config=config,
                context=KnowledgeRuntimeContext(
                    company_id=context.company_id,
                    top_k=self._settings.top_k,
                    similarity_score=self._settings.similarity_score,
                    chunk_preview_length=self._settings.chunk_preview_length,
                ),
                stream_mode="values",
            ):
                last_state = state
        except GraphRecursionError:
            logger.warning(
                "Knowledge retrieval hit the recursion limit; using the passages found so far"
            )
        except Exception:
            logger.exception(
                "Knowledge retrieval failed; using the passages found so far"
            )
        return last_state.get("chunks") or []

    async def _read_history(self, config: RunnableConfig) -> list[ConversationTurn]:
        snapshot = await self._retrieval_graph.aget_state(config)
        return (snapshot.values or {}).get("history", [])[
            -self._settings.history_turns :
        ]

    def _build_config(self, context: KnowledgeAgentContext) -> RunnableConfig:
        return {
            "recursion_limit": self._settings.max_recursion_limit,
            "configurable": {
                "thread_id": f"{context.conversation_id}:{self.name}",
                "knowledge_base": self._knowledge_base,
            },
        }
