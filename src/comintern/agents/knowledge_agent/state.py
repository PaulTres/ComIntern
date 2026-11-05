from typing import Annotated

from deepagents.graph import DeepAgentState

from comintern.agents.knowledge_agent.helpers import merge_chunks
from comintern.models.knowledge import Chunk, ConversationTurn


class KnowledgeAgentState(DeepAgentState):
    """
    `chunks` is filled only by the retrieval tool, so the sources can only name passages
    that were actually retrieved. `history` keeps the answered turns apart from `messages`,
    so the retrieval agent, which never answers, does not read the answers.
    """

    chunks: Annotated[list[Chunk], merge_chunks]
    history: list[ConversationTurn]
