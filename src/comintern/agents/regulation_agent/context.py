from dataclasses import dataclass

from comintern.agents.agent import RegulationReference
from comintern.models.chat import Audience
from comintern.models.knowledge import ConversationTurn


@dataclass(frozen=True, slots=True, kw_only=True)
class RegulationAgentContext:
    """One regulation-agent turn."""

    question: str
    company_id: int
    regulation_code: str | None
    applicable_regulations: tuple[RegulationReference, ...]
    history: tuple[ConversationTurn, ...]
    audience: Audience | None
