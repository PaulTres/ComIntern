"""The functions that run each sub-agent for a turn the orchestrator handed to it.

An invoker builds the sub-agent's own context from the orchestrator's turn and passes its
events on as they come. The lifespan binds each one to its agent with functools.partial.
"""

from collections.abc import AsyncIterator, Callable

from comintern.agents.agent import AgentEvent
from comintern.agents.knowledge_agent.agent import KnowledgeAgent
from comintern.agents.knowledge_agent.context import KnowledgeAgentContext
from comintern.agents.orchestrator.context import OrchestratorContext
from comintern.agents.regulation_agent.agent import RegulationAgent
from comintern.agents.regulation_agent.context import RegulationAgentContext

Invoker = Callable[[OrchestratorContext], AsyncIterator[AgentEvent]]


async def invoke_knowledge_agent(
    agent: KnowledgeAgent, context: OrchestratorContext
) -> AsyncIterator[AgentEvent]:
    async for event in agent.astream(
        KnowledgeAgentContext(
            question=context.question,
            company_id=context.company_id,
            conversation_id=context.conversation_id,
            audience=context.audience,
        )
    ):
        yield event


async def invoke_regulation_agent(
    agent: RegulationAgent, context: OrchestratorContext
) -> AsyncIterator[AgentEvent]:
    async for event in agent.astream(
        RegulationAgentContext(
            question=context.question,
            company_id=context.company_id,
            regulation_code=context.regulation_code,
            applicable_regulations=context.applicable_regulations,
            history=context.history,
            audience=context.audience,
        )
    ):
        yield event


__all__ = ["Invoker", "invoke_knowledge_agent", "invoke_regulation_agent"]
