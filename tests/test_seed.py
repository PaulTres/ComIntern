import asyncio
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore
from sqlalchemy.ext.asyncio import create_async_engine

from comintern.database.session_factory import SessionFactory
from comintern.models.auth import LoginRequestModel
from comintern.schemas import Base
from comintern.seed import seed_demo_account
from comintern.services.auth_service import AuthService
from comintern.services.catalog_service import CatalogService
from comintern.services.company_service import CompanyService
from comintern.services.knowledge_base import KnowledgeBase
from tests.conftest import build_test_settings


def test_demo_account_is_seeded_once_and_assessed(tmp_path: Path) -> None:
    settings = build_test_settings(tmp_path)

    async def scenario() -> None:
        engine = create_async_engine(settings.database.url)
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = SessionFactory(engine)
        await CatalogService(
            session_factory,
            KnowledgeBase(
                InMemoryVectorStore(DeterministicFakeEmbedding(size=16)),
                settings.chunking,
            ),
            tmp_path,
        ).seed()

        for _ in range(2):
            await seed_demo_account(
                session_factory, settings.demo_account, settings.jwt
            )

        signed_in = await AuthService(session_factory, settings.jwt).login(
            LoginRequestModel(
                email=settings.demo_account.email,
                password=settings.demo_account.password,
            )
        )
        assert signed_in.user.company.assessed_at is not None
        regulations = await CompanyService(session_factory).list_applicable_regulations(
            signed_in.user.company.id
        )
        assert {"EU_GDPR", "EU_NIS2", "RO_NIS2"} <= {r.code for r in regulations}
        await engine.dispose()

    asyncio.run(scenario())
