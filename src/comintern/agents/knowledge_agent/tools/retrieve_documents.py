from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolRuntime
from langgraph.types import Command

from comintern.agents.knowledge_agent.context import KnowledgeRuntimeContext
from comintern.agents.knowledge_agent.prompts import (
    NO_CHUNKS_TEXT,
    RETRIEVE_DOCUMENTS_DESCRIPTION,
    RETRIEVE_DOCUMENTS_TOOL,
    SEARCH_QUERY_DESCRIPTION,
)
from comintern.agents.knowledge_agent.state import KnowledgeAgentState
from comintern.services.knowledge_base import KnowledgeBase


@tool(RETRIEVE_DOCUMENTS_TOOL, description=RETRIEVE_DOCUMENTS_DESCRIPTION)
async def retrieve_documents(
    query: Annotated[str, SEARCH_QUERY_DESCRIPTION],
    runtime: ToolRuntime[KnowledgeRuntimeContext, KnowledgeAgentState],
) -> Command:
    """
    Search the passages the caller's company may read.

    :param query: The search query.
    :param runtime: Gives the company, the retrieval settings and the knowledge base.
    :return: The passages added to the state, and a preview of them for the model.
    """
    knowledge_base: KnowledgeBase = runtime.config["configurable"]["knowledge_base"]
    context = runtime.context
    chunks = await knowledge_base.search(
        query, context.company_id, context.top_k, context.similarity_score
    )
    previews = (
        "\n\n".join(
            f"{chunk.title} (score {chunk.score:.2f})\n{chunk.text[: context.chunk_preview_length]}"
            for chunk in chunks
        )
        or NO_CHUNKS_TEXT
    )
    return Command(
        update={
            "chunks": chunks,
            "messages": [
                ToolMessage(content=previews, tool_call_id=runtime.tool_call_id)
            ],
        }
    )
