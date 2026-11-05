"""The API wired to SQLite, an in-memory vector store and a fake chat model: no Docker, no Ollama."""

from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.vectorstores import InMemoryVectorStore
from sqlalchemy.ext.asyncio import create_async_engine

from comintern.api.app import create_app
from comintern.api.lifespan import build_services
from comintern.configuration.config import Settings
from comintern.database.session_factory import SessionFactory
from comintern.schemas import Base
from comintern.services.catalog_service import CatalogService
from comintern.services.knowledge_base import KnowledgeBase

GREETING = "Hello! I can help with EU, German and Romanian regulations."


class FakeChatModel(GenericFakeChatModel):
    """Answers every call with the greeting; it never calls a tool."""

    def bind_tools(self, tools, **kwargs):
        return self


def build_test_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        database={"url": f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"},
        jwt={"secret_key": "test-secret-key-that-is-at-least-32-characters"},
        documents={
            "upload_directory": tmp_path / "uploads",
            "regulation_texts_directory": tmp_path / "texts",
        },
        vector_store={"url": "http://unused", "collection_name": "unused"},
        embeddings={"model_name": "fake", "size": 16},
        llm={"model_name": "fake", "base_url": "http://unused"},
    )


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = build_test_settings(tmp_path)

    @asynccontextmanager
    async def test_lifespan(app: FastAPI) -> AsyncGenerator[None]:
        # ponytail: create_all stands in for the migrations here; the real schema comes from Alembic.
        engine = create_async_engine(settings.database.url)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = SessionFactory(engine)
        vector_store = InMemoryVectorStore(
            DeterministicFakeEmbedding(size=settings.embeddings.size)
        )
        await CatalogService(
            session_factory,
            KnowledgeBase(vector_store, settings.chunking),
            settings.documents.regulation_texts_directory,
        ).seed()
        build_services(
            app,
            settings,
            session_factory,
            vector_store,
            FakeChatModel(messages=iter([GREETING] * 50)),
        )
        yield
        await engine.dispose()

    with TestClient(create_app(lifespan=test_lifespan)) as test_client:
        yield test_client
