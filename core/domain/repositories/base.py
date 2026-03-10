from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

CreateEntityT = TypeVar("CreateEntityT")
ReadEntityT = TypeVar("ReadEntityT")
UpdateEntityT = TypeVar("UpdateEntityT")


class RepositoryError(RuntimeError):
    """Base exception for repository operations."""

    pass


class NotFoundError(RepositoryError):
    """Raised when a requested entity is not found."""

    pass


class AbstractRepository(ABC, Generic[CreateEntityT, ReadEntityT, UpdateEntityT]):
    """Repository port — domain layer defines the contract, infrastructure implements.

    Generic params:
        CreateEntityT: Entity for creation input
        ReadEntityT:   Entity for read output
        UpdateEntityT: Entity for update input

    Spec parameter accepts any query specification object
    that implements an ``apply(stmt)`` method (e.g. QuerySpec, SpecChain).
    """

    @abstractmethod
    async def create(self, dto: CreateEntityT) -> ReadEntityT: ...

    @abstractmethod
    async def get_by_id(
        self, obj_id: int, *, spec: Any = None
    ) -> Optional[ReadEntityT]: ...

    @abstractmethod
    async def get_list(self, *, spec: Any = None) -> list[ReadEntityT]: ...

    @abstractmethod
    async def update_by_id(
        self, obj_id: int, dto: UpdateEntityT
    ) -> Optional[ReadEntityT]: ...

    @abstractmethod
    async def delete_by_id(self, obj_id: int) -> bool: ...

    @abstractmethod
    async def count(self, *, spec: Any = None) -> int: ...
