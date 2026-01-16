from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class UnitOfWork:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_maker()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self.session is not None
        try:
            if exc:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()