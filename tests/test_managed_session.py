import unittest

from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.database.session import ManagedSession


class _FakeSession(AsyncSession):
    def __init__(self) -> None:
        super().__init__()
        self.committed = False
        self.rolled_back = False
        self.closed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def close(self) -> None:
        self.closed = True


class ManagedSessionTransactionTest(unittest.IsolatedAsyncioTestCase):
    async def test_commit_path_closes_session_without_rollback(self) -> None:
        fake = _FakeSession()
        managed = ManagedSession(session_maker=lambda: fake)

        async with managed as session:
            await session.commit()

        self.assertTrue(fake.committed)
        self.assertFalse(fake.rolled_back)
        self.assertTrue(fake.closed)

    async def test_exception_path_rolls_back_and_closes_session(self) -> None:
        fake = _FakeSession()
        managed = ManagedSession(session_maker=lambda: fake)

        with self.assertRaises(RuntimeError):
            async with managed:
                raise RuntimeError("trigger rollback")

        self.assertFalse(fake.committed)
        self.assertTrue(fake.rolled_back)
        self.assertTrue(fake.closed)
