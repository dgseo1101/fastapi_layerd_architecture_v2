from typing import Type

from core.application.dtos.user_dto import (
    CreateUserRequestDto,
    UpdateUserRequestDto,
    UserResponseDto,
)
from core.infrastructure.database.models.user import UserModel
from core.infrastructure.repositories.base_repository import SQLAlchemyRepository
from core.specs.base import SpecChain
from core.specs.common import OrderBy, Paginate, Where


class UserRepository(
    SQLAlchemyRepository[
        UserModel, CreateUserRequestDto, UserResponseDto, UpdateUserRequestDto
    ],
):
    @property
    def model(self) -> Type[UserModel]:
        return UserModel

    @property
    def read_schema(self) -> Type[UserResponseDto]:
        return UserResponseDto

    # ---- domain-specific queries ----

    def _users_spec(self, page: int, page_size: int) -> SpecChain[UserModel]:
        return SpecChain(
            [
                OrderBy.of(self.model.id.desc()),
                Paginate(page=page, page_size=page_size),
            ]
        )

    def _active_users_spec(self, page: int, page_size: int) -> SpecChain[UserModel]:
        return SpecChain(
            [
                Where.of(self.model.deleted_at.is_(None)),
                OrderBy.of(self.model.id.desc()),
                Paginate(page=page, page_size=page_size),
            ]
        )

    async def get_active_users(
        self, page: int, page_size: int
    ) -> list[UserResponseDto]:
        return await self.get_list(spec=self._active_users_spec(page, page_size))

    async def get_users(self, page: int, page_size: int) -> list[UserResponseDto]:
        return await self.get_list(spec=self._users_spec(page, page_size))
