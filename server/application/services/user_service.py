from typing import Callable, List, cast

from dependency_injector.providers import Configuration
from sqlalchemy.ext.asyncio import AsyncSession

from core.application.dtos.user_dto import (
    CreateUserRequestDto,
    UpdateUserRequestDto,
    UserResponseDto,
)
from core.application.services.base_service import BaseService
from server.infrastructure.repositories.user_repository import UserRepository


class UserService(
    BaseService[CreateUserRequestDto, UserResponseDto, UpdateUserRequestDto]
):
    def __init__(
        self,
        session_factory,
        repo_class: Callable[[AsyncSession], UserRepository],
        config: Configuration,
    ) -> None:
        super().__init__(session_factory=session_factory, repo_class=repo_class)
        self._config = config

    def _create_repo(self, session: AsyncSession) -> UserRepository:
        return cast(UserRepository, self._repo_class(session))

    # ---- domain-specific operations ----

    async def get_active_users(
        self, page: int, page_size: int
    ) -> List[UserResponseDto]:
        async with self._session_factory() as session:
            repo = self._create_repo(session)
            return await repo.get_active_users(page=page, page_size=page_size)

    async def get_users(self, page: int, page_size: int) -> List[UserResponseDto]:
        async with self._session_factory() as session:
            repo = self._create_repo(session)
            return await repo.get_users(page=page, page_size=page_size)
