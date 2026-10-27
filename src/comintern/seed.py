"""`comintern-seed`: load the YAML catalog into PostgreSQL, and index it and the official
regulation texts into Qdrant. Run it after `alembic upgrade head`; running it again is safe."""

import asyncio
import logging

from comintern.configuration.config import get_settings
from comintern.configuration.log_config import setup_logging
from comintern.database.session_factory import SessionFactory, create_engine
from comintern.embedding.embedding_factory import EmbeddingFactory
from comintern.services.catalog_service import CatalogService
from comintern.services.knowledge_base import KnowledgeBase
from comintern.vector_store.vector_store_factory import VectorStoreFactory

logger = logging.getLogger(__name__)


async def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings.database)
    vector_store = VectorStoreFactory.create_vector_store(
        EmbeddingFactory.create_embedding(settings.embeddings), settings.vector_store
    )
    catalog_service = CatalogService(
        SessionFactory(engine),
        KnowledgeBase(vector_store, settings.chunking),
        settings.documents.regulation_texts_directory,
    )
    try:
        await catalog_service.seed()
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
