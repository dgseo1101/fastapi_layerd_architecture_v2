# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, List, Mapping, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from core.application.dtos.base import BaseRequest, BaseResponse
from core.infrastructure.repositories.base_repository import BaseRepository, QuerySpec
from core.infrastructure.database.unit_of_work import UnitOfWork

CreateDTO = TypeVar("CreateDTO", bound=BaseRequest)
UpdateDTO = TypeVar("UpdateDTO", bound=BaseRequest)
ResponseDTO = TypeVar("ResponseDTO", bound=BaseResponse)

UowFactory = Callable[[], UnitOfWork]


class RepoRegistry:
    def __init__(self, factories: Mapping[str, Any]) -> None:
        self._factories = factories

    def resolve(self, session: AsyncSession, key: str):
        factory = self._factories.get(key)
        if factory is None:
            raise KeyError(f"Repository factory not registered: {key}")

        return factory(session)


class BaseService(ABC, Generic[CreateDTO, ResponseDTO, UpdateDTO]):
    def __init__(
        self,
        uow_factory: UowFactory,
        repo_registry: RepoRegistry,
        base_repo_key: str,
    ) -> None:
        self._uow_factory = uow_factory
        self._repo_registry = repo_registry
        self._base_repo_key = base_repo_key
        self.logger = logging.getLogger(__name__)

    @property
    @abstractmethod
    def create_dto(self) -> Type[CreateDTO]:
        ...

    @property
    @abstractmethod
    def response_dto(self) -> Type[ResponseDTO]:
        ...

    @property
    @abstractmethod
    def update_dto(self) -> Type[UpdateDTO]:
        ...

    def repo(self, uow: UnitOfWork, key: str) -> BaseRepository:
        assert uow.session is not None
        return self._repo_registry.resolve(uow.session, key)

    def base_repo(self, uow: UnitOfWork) -> BaseRepository:
        return self.repo(uow, self._base_repo_key)

    async def create_data(self, create_data: CreateDTO) -> ResponseDTO:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            return await repo.create_data(create_data=create_data)

    async def create_datas(self, create_datas: List[CreateDTO]) -> List[ResponseDTO]:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            return await repo.create_datas(create_datas=create_datas)

    async def get_datas(
        self,
        page: int,
        page_size: int,
        spec: QuerySpec | None = None,
    ) -> List[ResponseDTO]:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            return await repo.get_datas(page=page, page_size=page_size, spec=spec)

    async def get_data_by_data_id(
        self,
        data_id: int,
        spec: QuerySpec | None = None,
    ) -> Optional[ResponseDTO]:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            return await repo.get_data_by_data_id(data_id=data_id, spec=spec)

    async def update_data_by_data_id(
        self,
        data_id: int,
        update_data: UpdateDTO,
    ) -> Optional[ResponseDTO]:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            return await repo.update_data_by_data_id(
                data_id=data_id,
                update_data=update_data,
            )

    async def delete_data_by_data_id(self, data_id: int) -> None:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            await repo.delete_data_by_data_id(data_id=data_id)

    async def count_datas(self, spec: QuerySpec | None = None) -> int:
        async with self._uow_factory() as uow:
            repo = self.base_repo(uow)
            return await repo.count_datas(spec=spec)
