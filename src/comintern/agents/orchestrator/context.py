from dataclasses import dataclass

from comintern.agents.agent import RegulationReference
from comintern.models.chat import Audience
from comintern.models.knowledge import ConversationTurn


@dataclass(frozen=True, slots=True, kw_only=True)
class OrchestratorContext:
    """
    One turn, as the chat endpoint resolves it before any model runs: the company, the
    regulations that apply to it, the conversation and the question.
    """

    company_id: int
    company_name: str
    applicable_regulations: tuple[RegulationReference, ...]
    conversation_id: int
    question: str
    regulation_code: str | None
    audience: Audience | None
    history: tuple[ConversationTurn, ...]
