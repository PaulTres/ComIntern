from collections.abc import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from comintern.agents.agent import Agent, AgentEvent
from comintern.agents.audience import AUDIENCE_INSTRUCTIONS
from comintern.agents.knowledge_agent.helpers import build_passages, build_sources
from comintern.agents.knowledge_agent.prompts import NO_HISTORY_TEXT, NO_PASSAGES_TEXT
from comintern.agents.regulation_agent.context import RegulationAgentContext
from comintern.agents.regulation_agent.prompts import (
    NO_APPLICABLE_REGULATIONS,
    REGULATION_INPUT_TEMPLATE,
    REGULATION_SYSTEM_PROMPT,
    WHICH_REGULATION,
)
from comintern.configuration.config import RegulationAgentSettings
from comintern.models.chat import AgentName
from comintern.models.compliance import RegulationDetailResponseModel
from comintern.models.stream import (
    DeltaEventModel,
    PayloadEventModel,
    ProgressEventModel,
    ProgressStep,
)
from comintern.services.compliance_service import ComplianceService
from comintern.services.knowledge_base import KnowledgeBase

REGULATION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", REGULATION_SYSTEM_PROMPT), ("human", REGULATION_INPUT_TEMPLATE)]
)


def describe_checklist(detail: RegulationDetailResponseModel) -> str:
    """
    :return: One line per requirement: status, weight, evidence, note, what it asks and what proves it.
    """
    lines = []
    for requirement in detail.requirements:
        note = f", note: {requirement.note}" if requirement.note else ""
        lines.append(
            f"- [{requirement.status.value}] {requirement.title} ({requirement.reference or 'no reference'}), "
            f"weight {requirement.weight}, {len(requirement.documents)} evidence document(s){note}. "
            f"What it asks: {requirement.description} Evidence that proves it: {requirement.evidence_hint or 'not specified'}."
        )
    return "\n".join(lines)


class RegulationAgent(Agent[RegulationAgentContext]):
    """
    The agent for one regulation the company falls under: it reads the company's own checklist
    and the regulation's texts, and coaches the next steps.

    It is one class configured per regulation by the turn, which is how the board's "agents for
    each individual one" is built without a copy per regulation. It reads before it writes,
    with no tool loop, so it stays reliable on small local models.
    """

    name = AgentName.REGULATION_AGENT
    description = (
        "Coaches the company through one regulation: its gaps, next steps and evidence."
    )

    def __init__(
        self,
        chat_model: BaseChatModel,
        compliance_service: ComplianceService,
        knowledge_base: KnowledgeBase,
        settings: RegulationAgentSettings,
    ) -> None:
        self._compliance_service = compliance_service
        self._knowledge_base = knowledge_base
        self._settings = settings
        self._answer_chain = (
            REGULATION_PROMPT | chat_model | StrOutputParser()
        ).with_config(run_name="regulation_answer")

    async def astream(
        self, context: RegulationAgentContext
    ) -> AsyncIterator[AgentEvent]:
        """
        :param context: The question, the regulation it is about and the company.
        :return: Progress, the answer in pieces, then the sources; or a question back when the
            regulation is unknown or does not apply.
        """
        if context.regulation_code not in {
            regulation.code for regulation in context.applicable_regulations
        }:
            yield DeltaEventModel(text=self._ask_which_regulation(context))
            return

        yield ProgressEventModel(step=ProgressStep.READING_STATUS)
        detail = await self._compliance_service.get_regulation_detail(
            context.company_id, context.regulation_code
        )

        yield ProgressEventModel(step=ProgressStep.SEARCHING)
        chunks = await self._knowledge_base.search(
            f"{detail.short_name}: {context.question}",
            context.company_id,
            self._settings.top_k,
            self._settings.similarity_score,
            regulation_code=detail.code,
        )

        yield ProgressEventModel(step=ProgressStep.WRITING)
        history = context.history[-self._settings.history_turns :]
        async for piece in self._answer_chain.astream(
            {
                "short_name": detail.short_name,
                "regulation_name": detail.name,
                "audience": AUDIENCE_INSTRUCTIONS[context.audience],
                "history": "\n".join(
                    f"User: {turn.question}\nAssistant: {turn.answer}"
                    for turn in history
                )
                or NO_HISTORY_TEXT,
                "score": f"{detail.score.score}%"
                if detail.score.score is not None
                else "not scored yet",
                "reasons": " ".join(detail.reasons),
                "checklist": describe_checklist(detail),
                "passages": "\n\n".join(
                    f"({title})\n{text}" for title, text in build_passages(chunks)
                )
                or NO_PASSAGES_TEXT,
                "question": context.question,
            }
        ):
            yield DeltaEventModel(text=piece)
        if chunks:
            yield PayloadEventModel(value=build_sources(chunks))

    @staticmethod
    def _ask_which_regulation(context: RegulationAgentContext) -> str:
        if not context.applicable_regulations:
            return NO_APPLICABLE_REGULATIONS
        return WHICH_REGULATION.format(
            regulations=", ".join(
                regulation.short_name for regulation in context.applicable_regulations
            )
        )
