"""The base class every agent inherits: what it is handed, and what it yields back."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from comintern.models.chat import AgentName
from comintern.models.stream import (
    DeltaEventModel,
    PayloadEventModel,
    ProgressEventModel,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegulationReference:
    """A regulation that applies to the caller's company, as the agents name it."""

    code: str
    short_name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class HandOffEvent:
    """The orchestrator handing the turn to a sub-agent; recorded, never streamed."""

    agent: AgentName


AgentEvent = ProgressEventModel | DeltaEventModel | PayloadEventModel | HandOffEvent


class Agent[ContextT](ABC):
    """
    The orchestrator or one of the sub-agents it hands turns to.

    ContextT is what the agent is handed for one turn.
    """

    name: AgentName
    description: str

    @abstractmethod
    def astream(self, context: ContextT) -> AsyncIterator[AgentEvent]:
        """
        Handle one turn, yielding events as the work happens.

        :param context: What the agent is handed for this turn.
        :return: Progress and deltas in any number, and at most one payload.
        """
