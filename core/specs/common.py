from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from sqlalchemy import Select
from sqlalchemy.orm import selectinload

from .base import QuerySpec

ModelT = TypeVar("ModelT")

@dataclass(frozen=True)
class Where(Generic[ModelT]):
    priority: int = 10
    conditions: tuple[Any, ...] = ()

    @classmethod
    def of(cls, *conditions: Any) -> "Where[ModelT]":
        return cls(conditions=tuple(conditions))

    def apply(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        return stmt.where(*self.conditions)

@dataclass(frozen=True)
class OrderBy(Generic[ModelT]):
    priority: int = 30
    orders: tuple[Any, ...] = ()

    @classmethod
    def of(cls, *orders: Any) -> "OrderBy[ModelT]":
        return cls(orders=tuple(orders))

    def apply(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        return stmt.order_by(*self.orders)

@dataclass(frozen=True)
class Paginate(Generic[ModelT]):
    priority: int = 40
    page: int = 1
    page_size: int = 20

    def apply(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        page = max(self.page, 1)
        size = max(self.page_size, 1)
        return stmt.offset((page - 1) * size).limit(size)

@dataclass(frozen=True)
class SelectInLoad(Generic[ModelT]):
    priority: int = 20
    relationships: tuple[Any, ...] = ()

    @classmethod
    def of(cls, *relationships: Any) -> "SelectInLoad[ModelT]":
        return cls(relationships=tuple(relationships))

    def apply(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        return stmt.options(*(selectinload(r) for r in self.relationships))