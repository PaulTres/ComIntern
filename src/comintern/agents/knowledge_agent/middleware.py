from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from comintern.agents.knowledge_agent.state import KnowledgeAgentState


class TurnLimitMiddleware(AgentMiddleware):
    """
    Keep the retrieval agent's saved messages to the conversation's last turns.

    Every turn adds its question, its tool calls and the chunk previews to the
    conversation's thread, and the model reads all of them on every call. Before a
    model call, the messages of the turns older than the last history_turns earlier
    ones are deleted from the thread, so what the model reads, and what is saved,
    stays bounded however long the conversation runs. A turn starts at its question,
    so a tool call is never kept without its result.
    """

    def __init__(self, history_turns: int) -> None:
        """
        Fix how many earlier turns are kept.

        :param history_turns: How many turns before the current one are kept.
        """
        super().__init__()
        self._history_turns = history_turns

    def before_model(
        self, state: KnowledgeAgentState, runtime: Runtime
    ) -> dict[str, Any] | None:
        """
        Delete the messages of the turns older than the ones kept.

        :param state: The retrieval agent's state, with the conversation's messages.
        :param runtime: The run's runtime; not used.
        :return: The kept messages, replacing every saved one; None when no turn is
            old enough to delete.
        """
        messages = state["messages"]
        question_positions = [
            position
            for position, message in enumerate(messages)
            if isinstance(message, HumanMessage)
        ]
        kept_turn_count = self._history_turns + 1
        if len(question_positions) <= kept_turn_count:
            return None

        first_kept_position = question_positions[-kept_turn_count]
        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *messages[first_kept_position:],
            ]
        }
