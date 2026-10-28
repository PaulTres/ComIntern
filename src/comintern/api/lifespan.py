"""The composition root: every long-lived resource is built once here and put on app.state."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langgraph.checkpoint.memory import InMemorySaver

from comintern.agents.harness_profile import disable_general_purpose_subagent
from comintern.agents.knowledge_agent.agent import KnowledgeAgent
from comintern.agents.orchestrator.agent import OrchestratorAgent
from comintern.agents.orchestrator.invokers import (
    invoke_knowledge_agent,
    invoke_regulation_agent,
)
from comintern.agents.regulation_agent.agent import RegulationAgent
from comintern.configuration.config import Settings, get_settings
from comintern.configuration.log_config import setup_logging
from comintern.database.session_factory import SessionFactory, create_engine
from comintern.embedding.embedding_factory import EmbeddingFactory
from comintern.llm.llm_factory import LLMFactory
from comintern.models.chat import AgentName
from comintern.services.auth_service import AuthService
from comintern.services.chat_service import ChatService
from comintern.services.company_service import CompanyService
from comintern.services.compliance_service import ComplianceService
from comintern.services.document_service import DocumentService
from comintern.services.knowledge_base import KnowledgeBase
from comintern.vector_store.vector_store_factory import VectorStoreFactory

logger = logging.getLogger(__name__)


def build_services(
    app: FastAPI,
    settings: Settings,
    session_factory: SessionFactory,
    vector_store: VectorStore,
    chat_model: BaseChatModel,
) -> None:
    """
    Build the services and the agents on top of the shared resources, and publish them on app.state.

    The tests call it with an in-memory store and a fake model.
    """
    knowledge_base = KnowledgeBase(vector_store, settings.chunking)
    compliance_service = ComplianceService(session_factory)
    # ponytail: conversation memory of the agents lives in RAM and is lost on restart; the
    # messages themselves are in PostgreSQL. Swap in a PostgreSQL checkpointer if that matters.
    checkpointer = InMemorySaver()
    knowledge_agent = KnowledgeAgent(
        chat_model, knowledge_base, settings.knowledge_agent, checkpointer
    )
    regulation_agent = RegulationAgent(
        chat_model, compliance_service, knowledge_base, settings.regulation_agent
    )
    orchestrator = OrchestratorAgent(
        chat_model,
        settings.orchestrator_agent,
        {
            AgentName.KNOWLEDGE_AGENT: partial(invoke_knowledge_agent, knowledge_agent),
            AgentName.REGULATION_AGENT: partial(
                invoke_regulation_agent, regulation_agent
            ),
        },
        checkpointer,
    )

    app.state.settings = settings
    app.state.auth_service = AuthService(session_factory, settings.jwt)
    app.state.company_service = CompanyService(session_factory)
    app.state.compliance_service = compliance_service
    app.state.document_service = DocumentService(
        session_factory, settings.documents, knowledge_base
    )
    app.state.chat_service = ChatService(session_factory, orchestrator)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Build the engine, the providers, the services and the agents; dispose the engine on shutdown."""
    settings = get_settings()
    setup_logging(settings.logging.level)
    logger.info("Application startup")

    engine = create_engine(settings.database)
    disable_general_purpose_subagent(settings.llm.provider)
    embeddings = EmbeddingFactory.create_embedding(settings.embeddings)
    build_services(
        app,
        settings,
        SessionFactory(engine),
        VectorStoreFactory.create_vector_store(embeddings, settings.vector_store),
        LLMFactory.create_chat_model(settings.llm),
    )
    try:
        yield
    finally:
        await engine.dispose()
        logger.info("Application shutdown")
