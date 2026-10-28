from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comintern.schemas import RegulatoryUpdate


class UpdateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, regulation_code: str | None = None) -> list[RegulatoryUpdate]:
        statement = select(RegulatoryUpdate).order_by(
            RegulatoryUpdate.published_on.desc()
        )
        if regulation_code:
            statement = statement.where(
                RegulatoryUpdate.regulation_code == regulation_code
            )
        return list(await self._session.scalars(statement))

    async def get_by_key(self, key: str) -> RegulatoryUpdate | None:
        return await self._session.scalar(
            select(RegulatoryUpdate).where(RegulatoryUpdate.key == key)
        )

    async def add(self, update: RegulatoryUpdate) -> None:
        self._session.add(update)
