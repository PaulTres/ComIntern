from dataclasses import dataclass

from comintern.models.chat import Audience


@dataclass(frozen=True, slots=True, kw_only=True)
class KnowledgeAgentContext:
    """One knowledge-agent turn."""

    question: str
    company_id: int
    conversation_id: int
    audience: Audience | None


@dataclass(frozen=True, slots=True, kw_only=True)
class KnowledgeRuntimeContext:
    """What the retrieval tool gets for one turn; the knowledge base reaches it through the run's config."""

    company_id: int
    top_k: int
    similarity_score: float
    chunk_preview_length: int
