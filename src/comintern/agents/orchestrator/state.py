import operator
from typing import Annotated, TypedDict

from deepagents import DeepAgentState


class HandOff(TypedDict):
    """One sub-agent the turn is handed to, with its part of the user's message."""

    agent_name: str
    request: str
    regulation_code: str | None


class OrchestratorAgentState(DeepAgentState):
    """
    Each route tool adds its hand-off; the model may call several in one reply, so the
    list adds up what they write.
    """

    hand_offs: Annotated[list[HandOff], operator.add]
