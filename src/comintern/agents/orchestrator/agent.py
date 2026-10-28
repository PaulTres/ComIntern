import logging
from collections.abc import AsyncIterator, Mapping
from dataclasses import replace
from typing import Any, cast

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Overwrite

from comintern.agents.agent import Agent, AgentEvent, HandOffEvent
from comintern.agents.agent_catalog import OrchestratorTool
from comintern.agents.orchestrator.context import OrchestratorContext
from comintern.agents.orchestrator.invokers import Invoker
from comintern.agents.orchestrator.middleware import build_prompt_middleware
from comintern.agents.orchestrator.state import HandOff, OrchestratorAgentState
from comintern.agents.orchestrator.tools import ORCHESTRATOR_TOOLS
from comintern.agents.tool_filter_middleware import ToolFilterMiddleware
from comintern.configuration.config import OrchestratorAgentSettings
from comintern.models.chat import AgentName, SourceResponseModel
from comintern.models.stream import (
    DeltaEventModel,
    PayloadEventModel,
    ProgressEventModel,
    ProgressStep,
)

logger = logging.getLogger(__name__)

CLARIFYING_QUESTION = (
    "I'm not sure I understood what you need. Could you tell me a bit more?"
)
REPLY_SEPARATOR = "\n\n"
"""Put between the replies of a turn split between several agents."""


class OrchestratorAgent(Agent[OrchestratorContext]):
    """
    Works out which sub-agent a turn belongs to and hands it over. It never answers a
    compliance question itself: it routes, asks one clarifying question, or answers a greeting.

    Built once with the invokers of every sub-agent and shared by every caller. Each
    conversation has its own checkpoint thread, so follow-ups are routed in context.
    """

    name = AgentName.ORCHESTRATOR_AGENT
    description = "Works out which sub-agent a turn belongs to and hands it over."

    def __init__(
        self,
        chat_model: BaseChatModel,
        settings: OrchestratorAgentSettings,
        invokers: Mapping[AgentName, Invoker],
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._invokers = dict(invokers)
        self._settings = settings
        self._graph = create_deep_agent(
            model=chat_model,
            tools=ORCHESTRATOR_TOOLS,
            # Left empty on purpose: build_prompt_middleware writes the prompt on every call.
            system_prompt="",
            state_schema=OrchestratorAgentState,
            context_schema=OrchestratorContext,
            middleware=[
                ToolFilterMiddleware({tool.value for tool in OrchestratorTool}),
                build_prompt_middleware(),
            ],
            checkpointer=checkpointer,
        )

    async def astream(self, context: OrchestratorContext) -> AsyncIterator[AgentEvent]:
        """
        Decide who answers the turn, then stream that answer.

        :param context: The turn, resolved by the chat endpoint.
        :return: Progress, each hand-off and its sub-agent's events, or the orchestrator's own reply.
        """
        config: RunnableConfig = {
            "configurable": {"thread_id": f"{context.conversation_id}:{self.name}"},
            "recursion_limit": self._settings.max_recursion_limit,
        }
        yield ProgressEventModel(step=ProgressStep.CLASSIFYING)
        state = await self._graph.ainvoke(
            cast(
                Any,
                {
                    "messages": [HumanMessage(context.question)],
                    "hand_offs": Overwrite([]),
                },
            ),
            config=config,
            context=context,
        )
        match state:
            case {"hand_offs": hand_offs} if hand_offs:
                async for event in self._run_hand_offs(context, hand_offs):
                    yield event
            case {"messages": messages} if (
                messages and isinstance(messages[-1], AIMessage) and messages[-1].text
            ):
                yield DeltaEventModel(text=messages[-1].text)
            case _:
                yield DeltaEventModel(text=CLARIFYING_QUESTION)

    async def _run_hand_offs(
        self, context: OrchestratorContext, hand_offs: list[HandOff]
    ) -> AsyncIterator[AgentEvent]:
        """
        Run the sub-agents in order. A single sub-agent gets the user's own message; only a
        message split between several gives each its part. Their sources are merged into the
        one payload a turn sends.
        """
        best_sources: dict[str, SourceResponseModel] = {}
        for index, hand_off in enumerate(hand_offs):
            agent_name = AgentName(hand_off["agent_name"])
            if index > 0:
                yield DeltaEventModel(text=REPLY_SEPARATOR)
            yield HandOffEvent(agent=agent_name)
            agent_context = replace(
                context,
                question=hand_off["request"]
                if len(hand_offs) > 1
                else context.question,
                regulation_code=hand_off.get("regulation_code")
                or context.regulation_code,
            )
            async for event in self._invokers[agent_name](agent_context):
                if isinstance(event, PayloadEventModel):
                    for source in event.value:
                        if (
                            source.title not in best_sources
                            or source.score > best_sources[source.title].score
                        ):
                            best_sources[source.title] = source
                    continue
                yield event
        if best_sources:
            yield PayloadEventModel(
                value=sorted(
                    best_sources.values(), key=lambda source: source.score, reverse=True
                )
            )
