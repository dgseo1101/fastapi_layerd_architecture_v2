from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, Sequence, TypeVar
from sqlalchemy import Select

ModelT = TypeVar("ModelT")


class QuerySpec(Protocol[ModelT]):
    @property
    def priority(self) -> int: ...

    def apply(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]: ...


@dataclass(frozen=True)
class SpecChain(Generic[ModelT]):
    specs: Sequence[QuerySpec[ModelT]]

    def apply(self, stmt: Select[tuple[ModelT]]) -> Select[tuple[ModelT]]:
        for s in sorted(self.specs, key=lambda x: getattr(x, "priority", 100)):
            stmt = s.apply(stmt)
        return stmt
