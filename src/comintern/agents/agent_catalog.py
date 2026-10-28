"""The sub-agents the orchestrator can hand turns to, and what each handles."""

from enum import StrEnum

from comintern.models.chat import AgentName


class OrchestratorTool(StrEnum):
    """The orchestrator's route tools."""

    ROUTE_TO_KNOWLEDGE_AGENT = "ROUTE_TO_KNOWLEDGE_AGENT"
    ROUTE_TO_REGULATION_AGENT = "ROUTE_TO_REGULATION_AGENT"


AGENTS: dict[AgentName, tuple[OrchestratorTool, str]] = {
    AgentName.KNOWLEDGE_AGENT: (
        OrchestratorTool.ROUTE_TO_KNOWLEDGE_AGENT,
        (
            "what a regulation says in general: its scope, definitions, articles, deadlines, fines, authorities, "
            "and how regulations overlap; also what the company's own uploaded documents say"
        ),
    ),
    AgentName.REGULATION_AGENT: (
        OrchestratorTool.ROUTE_TO_REGULATION_AGENT,
        (
            "the company's own position on one regulation: what is missing, what to do next, priorities, which "
            "evidence to upload, how to fix a requirement"
        ),
    ),
}
