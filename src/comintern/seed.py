"""`comintern-seed`: load the YAML catalog into PostgreSQL, create the demo login, and index the
catalog and the official regulation texts into Qdrant. Run it after `alembic upgrade head`; running
it again is safe."""

import asyncio
import logging

from comintern import catalog
from comintern.configuration.config import (
    DemoAccountSettings,
    JWTSettings,
    get_settings,
)
from comintern.configuration.log_config import setup_logging
from comintern.database.session_factory import SessionFactory, create_engine
from comintern.embedding.embedding_factory import EmbeddingFactory
from comintern.exceptions import AppError, AppErrorCode
from comintern.models.auth import CompanyUpdateRequestModel, RegisterRequestModel
from comintern.services.auth_service import AuthService
from comintern.services.catalog_service import CatalogService
from comintern.services.company_service import CompanyService
from comintern.services.knowledge_base import KnowledgeBase
from comintern.vector_store.vector_store_factory import VectorStoreFactory

logger = logging.getLogger(__name__)


async def seed_demo_account(
    session_factory: SessionFactory,
    demo_settings: DemoAccountSettings,
    jwt_settings: JWTSettings,
) -> None:
    """
    Sign up the demo company and answer its questionnaire, through the same services as a real
    user. An existing demo account is left as it is, with whatever was changed in it.
    """
    company = catalog.demo_company()
    try:
        signed_up = await AuthService(session_factory, jwt_settings).register(
            RegisterRequestModel(
                email=demo_settings.email,
                password=demo_settings.password,
                company_name=company["name"],
            )
        )
    except AppError as error:
        if error.error is not AppErrorCode.EMAIL_ALREADY_REGISTERED:
            raise
        logger.info("The demo account %s already exists", demo_settings.email)
        return
    await CompanyService(session_factory).update_company(
        signed_up.user.company.id,
        CompanyUpdateRequestModel(profile=company["profile"]),
    )
    logger.info("Created the demo account %s", demo_settings.email)


async def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings.database)
    session_factory = SessionFactory(engine)
    vector_store = VectorStoreFactory.create_vector_store(
        EmbeddingFactory.create_embedding(settings.embeddings), settings.vector_store
    )
    catalog_service = CatalogService(
        session_factory,
        KnowledgeBase(vector_store, settings.chunking),
        settings.documents.regulation_texts_directory,
    )
    try:
        await catalog_service.seed()
        if settings.demo_account.enabled:
            await seed_demo_account(
                session_factory, settings.demo_account, settings.jwt
            )
        passage_count = await catalog_service.index()
        logger.info(
            "Indexed %s passages of the catalog and the official texts", passage_count
        )
    finally:
        await engine.dispose()


def main() -> None:
    setup_logging(get_settings().logging.level)
    asyncio.run(seed())


if __name__ == "__main__":
    main()
