from __future__ import annotations

from typing import Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class ManagedSession:
    """Async context manager that yields an AsyncSession directly.

    Auto-rollback on exception, always closes the session on exit.

    Usage::

        async with session_factory() as session:
            repo = SomeRepository(session)
            await repo.create(dto)
            await session.commit()          # explicit commit required
            # if an exception is raised before commit(), auto-rollback kicks in
    """

    def __init__(self, session_maker: Callable[[], AsyncSession]) -> None:
        self._session_maker = session_maker
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        self._session = self._session_maker()
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        assert self._session is not None
        try:
            if exc:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None
