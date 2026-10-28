"""The route tools: each records a hand-off and ends the orchestrator's run."""

import logging
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command

from comintern.agents.agent_catalog import OrchestratorTool
from comintern.agents.orchestrator.context import OrchestratorContext
from comintern.agents.orchestrator.state import HandOff, OrchestratorAgentState
from comintern.models.chat import AgentName

logger = logging.getLogger(__name__)

HAND_OFF_MESSAGE = "Handed off to the {agent_name}."
REQUEST_DESCRIPTION = "What the user's latest message asks of this agent, in the user's words. Leave out the parts other agents handle."
REASON_DESCRIPTION = "One short sentence: why this message belongs to this agent."


def _hand_off(
    agent_name: AgentName,
    request: str,
    regulation_code: str | None,
    runtime: ToolRuntime[OrchestratorContext, OrchestratorAgentState],
) -> Command:
    logger.info(
        "Handing off agent_name=%s regulation_code=%s", agent_name, regulation_code
    )
    return Command(
        update={
            "hand_offs": [
                HandOff(
                    agent_name=agent_name.value,
                    request=request,
                    regulation_code=regulation_code,
                )
            ],
            "messages": [
                ToolMessage(
                    content=HAND_OFF_MESSAGE.format(agent_name=agent_name),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@tool(
    OrchestratorTool.ROUTE_TO_KNOWLEDGE_AGENT,
    description=(
        "Send the question to the knowledge agent, which answers what a regulation says in general (scope, "
        "articles, deadlines, fines, overlaps) and what the company's uploaded documents say."
    ),
    return_direct=True,
)
async def route_to_knowledge_agent(
    request: Annotated[str, REQUEST_DESCRIPTION],
    reason: Annotated[str, REASON_DESCRIPTION],
    runtime: ToolRuntime[OrchestratorContext, OrchestratorAgentState],
) -> Command:
    """Route the question to the knowledge agent."""
    return _hand_off(AgentName.KNOWLEDGE_AGENT, request, None, runtime)


@tool(
    OrchestratorTool.ROUTE_TO_REGULATION_AGENT,
    description=(
        "Send the question to the agent of one regulation that applies to the company. It knows the company's "
        "checklist for that regulation and answers what is missing, what to do next and which evidence to upload."
    ),
    return_direct=True,
)
async def route_to_regulation_agent(
    request: Annotated[str, REQUEST_DESCRIPTION],
    regulation_code: Annotated[
        str,
        "The code of the regulation, exactly as in the list of regulations that apply, e.g. EU_GDPR.",
    ],
    reason: Annotated[str, REASON_DESCRIPTION],
    runtime: ToolRuntime[OrchestratorContext, OrchestratorAgentState],
) -> Command:
    """Route the question to the agent of one regulation."""
    return _hand_off(AgentName.REGULATION_AGENT, request, regulation_code, runtime)


ORCHESTRATOR_TOOLS = [route_to_knowledge_agent, route_to_regulation_agent]
