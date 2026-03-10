from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.repositories.base import AbstractRepository
from core.specs.base import QuerySpec, SpecChain

ModelT = TypeVar("ModelT")
CreateEntityT = TypeVar("CreateEntityT", bound=BaseModel)
ReadEntityT = TypeVar("ReadEntityT", bound=BaseModel)
UpdateEntityT = TypeVar("UpdateEntityT", bound=BaseModel)


class SQLAlchemyRepository(
    AbstractRepository[CreateEntityT, ReadEntityT, UpdateEntityT],
    Generic[ModelT, CreateEntityT, ReadEntityT, UpdateEntityT],
):
    """SQLAlchemy implementation of AbstractRepository.

    Subclass MUST define:
        model       — SQLAlchemy ORM model class
        read_schema — Pydantic schema for read output

    Optionally override:
        pk_column       — primary key column name (default: "id")
        _to_read()      — ORM → Pydantic mapping
        _create_values() — CreateEntity → dict mapping
        _update_values() — UpdateEntity → dict mapping
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---- abstract properties (subclass MUST define) ----

    @property
    def model(self) -> Type[ModelT]:
        raise NotImplementedError("Repository subclass must define 'model'")

    @property
    def read_schema(self) -> Type[ReadEntityT]:
        raise NotImplementedError("Repository subclass must define 'read_schema'")

    # ---- overridable configuration ----

    @property
    def pk_column(self) -> str:
        """Override to change the primary key column name. Default: ``"id"``."""
        return "id"

    # ---- mapping hooks (override if needed) ----

    def _to_read(self, orm_obj: Any) -> ReadEntityT:
        return self.read_schema.model_validate(orm_obj, from_attributes=True)

    def _create_values(self, dto: CreateEntityT) -> dict[str, Any]:
        return dto.model_dump(exclude_none=True)

    def _update_values(self, dto: UpdateEntityT) -> dict[str, Any]:
        return dto.model_dump(exclude_none=True)

    # ---- query building ----

    def _base_select(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    def _pk_filter(self, obj_id: int) -> Any:
        """Build a primary-key equality filter."""
        return getattr(self.model, self.pk_column) == obj_id

    def _apply_spec(
        self,
        stmt: Select[tuple[ModelT]],
        spec: QuerySpec[ModelT] | SpecChain[ModelT] | None,
    ) -> Select[tuple[ModelT]]:
        if spec is None:
            return stmt
        return spec.apply(stmt)

    # ---- CRUD ----

    async def create(self, dto: CreateEntityT) -> ReadEntityT:
        obj = self.model(**self._create_values(dto))  # type: ignore[call-arg]
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return self._to_read(obj)

    async def get_by_id(
        self, obj_id: int, *, spec: Any = None
    ) -> Optional[ReadEntityT]:
        stmt = self._base_select().where(self._pk_filter(obj_id))
        stmt = self._apply_spec(stmt, spec)
        res = await self.session.execute(stmt)
        obj = res.scalars().first()
        return self._to_read(obj) if obj else None

    async def get_list(self, *, spec: Any = None) -> list[ReadEntityT]:
        stmt = self._apply_spec(self._base_select(), spec)
        res = await self.session.execute(stmt)
        return [self._to_read(x) for x in res.scalars().all()]

    async def count(self, *, spec: Any = None) -> int:
        stmt: Any = select(func.count()).select_from(self.model)
        if spec is not None:
            stmt = spec.apply(stmt)
        res = await self.session.execute(stmt)
        return int(res.scalar_one())

    async def update_by_id(
        self, obj_id: int, dto: UpdateEntityT
    ) -> Optional[ReadEntityT]:
        values = self._update_values(dto)
        if not values:
            return await self.get_by_id(obj_id)

        stmt = update(self.model).where(self._pk_filter(obj_id)).values(**values)
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_id(obj_id)

    async def delete_by_id(self, obj_id: int) -> bool:
        existing = await self.get_by_id(obj_id)
        if existing is None:
            return False

        stmt = delete(self.model).where(self._pk_filter(obj_id))
        await self.session.execute(stmt)
        await self.session.flush()
        return True
