from __future__ import annotations

from abc import ABC
from typing import Any, Callable, Generic, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.repositories.base import AbstractRepository
from core.infrastructure.database.session import ManagedSession
from core.application.dtos.base import BaseRequest, BaseResponse

CreateDTO = TypeVar("CreateDTO", bound=BaseRequest)
UpdateDTO = TypeVar("UpdateDTO", bound=BaseRequest)
ResponseDTO = TypeVar("ResponseDTO", bound=BaseResponse)


class BaseService(ABC, Generic[CreateDTO, ResponseDTO, UpdateDTO]):
    """Application service providing transactional CRUD with lifecycle hooks.

    Each public method opens its own session scope, executes the operation,
    and commits.  Internal ``_create`` / ``_update`` / ``_delete`` variants
    accept an existing ``AsyncSession`` so that subclasses can compose
    multiple operations within a **single transaction**.

    Constructor args:
        session_factory  — callable that returns a ``ManagedSession`` context manager
        repo_class       — primary repository class; instantiated with ``(session)``

    Optionally override hooks:
        validate_create / validate_update — pre-mutation validation
        after_create / after_update / after_delete — post-mutation side effects

    Multi-repo injection (Pattern 2)::

        class OrderService(BaseService[CreateOrderDto, OrderDto, UpdateOrderDto]):
            def __init__(self, session_factory, repo_class, *,
                         product_repo_class: type[ProductRepository] = ProductRepository):
                super().__init__(session_factory, repo_class)
                self._product_repo_class = product_repo_class

            def _create_repo(self, session) -> OrderRepository:
                return self._repo_class(session)  # type narrowing

            def _create_product_repo(self, session) -> ProductRepository:
                return self._product_repo_class(session)
    """

    def __init__(
        self,
        session_factory: Callable[..., ManagedSession],
        repo_class: Callable[
            [AsyncSession], AbstractRepository[CreateDTO, ResponseDTO, UpdateDTO]
        ],
    ) -> None:
        self._session_factory = session_factory
        self._repo_class = repo_class

    def _create_repo(
        self,
        session: AsyncSession,
    ) -> AbstractRepository[CreateDTO, ResponseDTO, UpdateDTO]:
        """Create the primary repo. Override in subclass to narrow the return type."""
        return self._repo_class(session)

    # ---- hooks (override optional) ----

    async def validate_create(self, dto: CreateDTO) -> None: ...
    async def validate_update(self, obj_id: int, dto: UpdateDTO) -> None: ...

    async def after_create(self, created: ResponseDTO) -> None: ...
    async def after_update(self, updated: Optional[ResponseDTO]) -> None: ...
    async def after_delete(self, obj_id: int, deleted: bool) -> None: ...

    # ---- internal (composable within the same transaction, NO commit) ----

    async def _create(self, session: AsyncSession, dto: CreateDTO) -> ResponseDTO:
        repo = self._create_repo(session)
        await self.validate_create(dto)
        created = await repo.create(dto)
        await self.after_create(created)
        return created

    async def _update(
        self,
        session: AsyncSession,
        obj_id: int,
        dto: UpdateDTO,
    ) -> Optional[ResponseDTO]:
        repo = self._create_repo(session)
        await self.validate_update(obj_id, dto)
        updated = await repo.update_by_id(obj_id, dto)
        await self.after_update(updated)
        return updated

    async def _delete(self, session: AsyncSession, obj_id: int) -> bool:
        repo = self._create_repo(session)
        deleted = await repo.delete_by_id(obj_id)
        await self.after_delete(obj_id, deleted)
        return deleted

    # ---- public API (one transaction per call) ----

    async def create(self, dto: CreateDTO) -> ResponseDTO:
        async with self._session_factory() as session:
            created = await self._create(session, dto)
            await session.commit()
            return created

    async def get_by_id(
        self, obj_id: int, *, spec: Any = None
    ) -> Optional[ResponseDTO]:
        async with self._session_factory() as session:
            repo = self._create_repo(session)
            return await repo.get_by_id(obj_id, spec=spec)

    async def get_list(self, *, spec: Any = None) -> list[ResponseDTO]:
        async with self._session_factory() as session:
            repo = self._create_repo(session)
            return await repo.get_list(spec=spec)

    async def update_by_id(
        self,
        obj_id: int,
        dto: UpdateDTO,
    ) -> Optional[ResponseDTO]:
        async with self._session_factory() as session:
            updated = await self._update(session, obj_id, dto)
            await session.commit()
            return updated

    async def delete_by_id(self, obj_id: int) -> bool:
        async with self._session_factory() as session:
            deleted = await self._delete(session, obj_id)
            await session.commit()
            return deleted

    async def count(self, *, spec: Any = None) -> int:
        async with self._session_factory() as session:
            repo = self._create_repo(session)
            return await repo.count(spec=spec)
