from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comintern.schemas import User


class UserRepository:
    """Reads and adds users. It never commits: the caller's session does."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def add(self, user: User) -> None:
        self._session.add(user)
        await self._session.flush()
