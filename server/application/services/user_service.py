import datetime
import logging
from pytz import timezone
from typing import List

from dependency_injector.providers import Configuration
from fastapi import HTTPException
import jwt
from passlib.context import CryptContext

from core.application.dtos.user_dto import (
    CreateUserRequestDto,
    UserResponseDto,
    UpdateUserRequestDto,
)
from core.application.services.base_service import BaseService
from core.infrastructure.database.unit_of_work import UnitOfWork
from core.application.services.base_service import RepoRegistry 


class UserService(BaseService):
    def __init__(self, uow_factory, repo_registry, config: Configuration) -> None:
        super().__init__(
            uow_factory=uow_factory,
            repo_registry=repo_registry,
            base_repo_key="user",
        )

    @property
    def create_dto(self):
        return CreateUserRequestDto

    @property
    def response_dto(self):
        return UserResponseDto

    @property
    def update_dto(self):
        return UpdateUserRequestDto

    async def get_activate_user(self, page: int, page_size: int) -> List[UserResponseDto]:
        async with self._uow_factory() as uow:
            user_repo = self.base_repo(uow)
            return await user_repo.get_activate_users(page=page, page_size=page_size)