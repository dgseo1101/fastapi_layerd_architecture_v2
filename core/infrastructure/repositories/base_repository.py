# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, List, Optional, Protocol, Sequence, Type, TypeVar

from sqlalchemy import Select, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.application.dtos.base import BaseRequest
from core.domain.entities.entity import Entity
from core.infrastructure.database.database import Base

CreateEntity = TypeVar("CreateEntity", bound=BaseRequest)
ReturnEntity = TypeVar("ReturnEntity", bound=Entity)
UpdateEntity = TypeVar("UpdateEntity", bound=BaseRequest)
ModelT = TypeVar("ModelT", bound=Base)

class QuerySpec(Protocol[ModelT]):
    def apply_select(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]: ...
    def apply_count(self, stmt: Select[tuple[int]]) -> Select[tuple[int]]: ...

class PaginationSpec:
    pass

@dataclass(frozen=True)
class SpecChain(Generic[ModelT]):
    specs: Sequence[QuerySpec[ModelT]]

    def apply_select(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        for s in self.specs:
            stmt = s.apply_select(stmt)
        return stmt

    def apply_count(self, stmt: Select[tuple[int]]) -> Select[tuple[int]]:
        for s in self.specs:
            stmt = s.apply_count(stmt)
        return stmt


@dataclass(frozen=True)
class Where(Generic[ModelT]):
    conditions: tuple[Any, ...]

    @classmethod
    def of(cls, *conditions: Any) -> "Where[ModelT]":
        return cls(conditions=tuple(conditions))

    def apply_select(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        return stmt.where(*self.conditions)

    def apply_count(self, stmt: Select[tuple[int]]) -> Select[tuple[int]]:
        return stmt.where(*self.conditions)


@dataclass(frozen=True)
class OrderBy(Generic[ModelT]):
    orders: tuple[Any, ...]

    @classmethod
    def of(cls, *orders: Any) -> "OrderBy[ModelT]":
        return cls(orders=tuple(orders))

    def apply_select(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        return stmt.order_by(*self.orders)

    def apply_count(self, stmt: Select[tuple[int]]) -> Select[tuple[int]]:
        return stmt 

@dataclass(frozen=True)
class SelectInLoad(Generic[ModelT]):
    relationships: tuple[Any, ...]

    @classmethod
    def of(cls, *relationships: Any) -> "SelectInLoad[ModelT]":
        return cls(relationships=tuple(relationships))

    def apply_select(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        return stmt.options(*(selectinload(r) for r in self.relationships))

    def apply_count(self, stmt: Select[tuple[int]]) -> Select[tuple[int]]:
        return stmt


@dataclass(frozen=True)
class Paginate(Generic[ModelT], PaginationSpec):
    page: int
    page_size: int

    def apply_select(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        offset = max(self.page - 1, 0) * self.page_size
        return stmt.offset(offset).limit(self.page_size)

    def apply_count(self, stmt: Select[tuple[int]]) -> Select[tuple[int]]:
        return stmt 


def _spec_has_paginate(spec: QuerySpec[Any] | None) -> bool:
    if spec is None:
        return False

    if isinstance(spec, PaginationSpec):
        return True

    if isinstance(spec, SpecChain):
        return any(isinstance(s, PaginationSpec) for s in spec.specs)

    return False


class BaseRepository(ABC, Generic[CreateEntity, ReturnEntity, UpdateEntity, ModelT]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    @abstractmethod
    def model(self) -> Type[ModelT]:
        ...

    @property
    @abstractmethod
    def create_entity(self) -> Type[CreateEntity]:
        ...

    @property
    @abstractmethod
    def return_entity(self) -> Type[ReturnEntity]:
        ...

    @property
    @abstractmethod
    def update_entity(self) -> Type[UpdateEntity]:
        ...

    def _base_select(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    def _base_count(self) -> Select[tuple[int]]:
        return select(func.count()).select_from(self.model)

    def _apply_spec_select(
        self,
        stmt: Select[tuple[ModelT]],
        spec: QuerySpec[ModelT] | None,
    ) -> Select[tuple[ModelT]]:
        return spec.apply_select(stmt) if spec is not None else stmt

    def _apply_spec_count(
        self,
        stmt: Select[tuple[int]],
        spec: QuerySpec[ModelT] | None,
    ) -> Select[tuple[int]]:
        return spec.apply_count(stmt) if spec is not None else stmt

    async def flush(self) -> None:
        await self._session.flush()

    async def refresh(self, obj: Any) -> None:
        await self._session.refresh(obj)

    async def create_data(self, create_data: CreateEntity) -> ReturnEntity:
        data = self.model(**create_data.model_dump(exclude_none=True))
        self._session.add(data)

        await self._session.flush()

        return self.return_entity(**vars(data))

    async def create_datas(self, create_datas: List[CreateEntity]) -> List[ReturnEntity]:
        values = [c.model_dump(exclude_none=True) for c in create_datas]

        result = await self._session.execute(insert(self.model).values(values))

        inserted_ids = [row[0] for row in result.inserted_primary_key_rows]

        if not inserted_ids:
            return []

        result = await self._session.execute(
            select(self.model).where(self.model.id.in_(inserted_ids))
        )
        datas = result.scalars().all()
        return [self.return_entity(**vars(data)) for data in datas]

    async def update_data_by_data_id(
        self,
        data_id: int,
        update_data: UpdateEntity,
    ) -> Optional[ReturnEntity]:
        result = await self._session.execute(
            select(self.model).where(self.model.id == data_id)
        )
        data = result.scalars().first()

        if not data:
            return None

        for key, value in update_data.model_dump(exclude_none=True).items():
            setattr(data, key, value)

        await self._session.flush()
        await self._session.refresh(data)

        return self.return_entity(**vars(data))

    async def delete_data_by_data_id(self, data_id: int) -> None:
        result = await self._session.execute(
            select(self.model).where(self.model.id == data_id)
        )
        data = result.scalars().first()

        if data:
            await self._session.delete(data)

    async def get_datas(
        self,
        page: int = None,
        page_size: int = None,
        spec: QuerySpec[ModelT] | None = None,
    ) -> List[ReturnEntity]:
        stmt = self._base_select()

        if not _spec_has_paginate(spec):
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        stmt = self._apply_spec_select(stmt, spec)

        result = await self._session.execute(stmt)
        datas = result.scalars().all()

        return [self.return_entity(**vars(data)) for data in datas]

    async def get_data_by_data_id(
        self,
        data_id: int,
        spec: QuerySpec[ModelT] | None = None,
    ) -> Optional[ReturnEntity]:
        stmt = self._base_select().where(self.model.id == data_id)
        stmt = self._apply_spec_select(stmt, spec)

        result = await self._session.execute(stmt)
        data = result.scalars().first()

        return self.return_entity(**vars(data)) if data else None

    async def get_datas_by_data_id(
        self,
        data_id: int,
        page: int,
        page_size: int,
        spec: QuerySpec[ModelT] | None = None,
    ) -> List[ReturnEntity]:
        stmt = self._base_select().where(self.model.id == data_id)

        if not _spec_has_paginate(spec):
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        stmt = self._apply_spec_select(stmt, spec)

        result = await self._session.execute(stmt)
        datas = result.scalars().all()

        return [self.return_entity(**vars(data)) for data in datas]

    async def count_datas(self, spec: QuerySpec[ModelT] | None = None) -> int:
        stmt = self._base_count()
        stmt = self._apply_spec_count(stmt, spec)

        result = await self._session.execute(stmt)
        return int(result.scalar_one())
