"""The engine and the one place a transaction is committed or rolled back."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from comintern.configuration.config import DatabaseSettings

logger = logging.getLogger(__name__)


def create_engine(database_settings: DatabaseSettings) -> AsyncEngine:
    """
    Build the application's single engine and its connection pool.

    :param database_settings: The connection URL and pool sizes.
    :return: The async engine; dispose it on shutdown.
    """
    return create_async_engine(
        database_settings.url,
        pool_pre_ping=True,
        pool_size=database_settings.pool_size,
        max_overflow=database_settings.max_overflow,
    )


class SessionFactory:
    """Hands out sessions bound to the shared engine."""

    def __init__(self, engine: AsyncEngine) -> None:
        """
        :param engine: The shared async engine.
        """
        self._session_maker = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        """
        Yield a session, commit when the block succeeds, roll back when it raises.

        Services open the session; repositories receive it and never commit.

        :return: An async generator yielding one session.
        """
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                logger.info("Rolling back session")
                await session.rollback()
                raise
