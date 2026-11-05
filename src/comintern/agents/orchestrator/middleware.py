"""The middleware that writes the orchestrator's system prompt on every model call."""

from datetime import UTC, datetime
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, dynamic_prompt

from comintern.agents.agent_catalog import AGENTS
from comintern.agents.orchestrator.context import OrchestratorContext
from comintern.agents.orchestrator.prompts import ORCHESTRATOR_SYSTEM_PROMPT


def build_prompt_middleware() -> AgentMiddleware[Any, Any]:
    """
    :return: The middleware filling the prompt with today's date, the agents, the company and
        the regulations that apply to it.
    """

    @dynamic_prompt
    def system_prompt(request: ModelRequest[OrchestratorContext]) -> str:
        context = request.runtime.context
        names = {
            regulation.code: regulation.short_name
            for regulation in context.applicable_regulations
        }
        return ORCHESTRATOR_SYSTEM_PROMPT.format(
            today=datetime.now(UTC).strftime("%Y-%m-%d"),
            agents="\n".join(
                f"- {agent_name} ({tool_name}): {handles}"
                for agent_name, (tool_name, handles) in AGENTS.items()
            ),
            company_name=context.company_name,
            regulations=", ".join(f"{code}: {name}" for code, name in names.items())
            or "none yet",
            current_regulation=names.get(
                context.regulation_code or "", "no particular regulation"
            ),
        )

    return system_prompt
