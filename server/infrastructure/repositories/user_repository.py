from typing import List

from core.infrastructure.database.models.user import UserModel
from core.infrastructure.repositories.base_repository import (
    BaseRepository, 
    SpecChain, 
    Where,
    OrderBy,
    Paginate
)

from core.domain.entities.user_entity import (
    UserEntity,
    CreateUserEntity,
    UpdateUserEntity,
)

class UserRepository(BaseRepository[CreateUserEntity, UserEntity, UpdateUserEntity, UserModel]):
    @property
    def model(self):
        return UserModel

    @property
    def create_entity(self):
        return CreateUserEntity

    @property
    def return_entity(self):
        return UserEntity

    @property
    def update_entity(self):
        return UpdateUserEntity

    def _active_users_spec(self, page: int, page_size: int):
        return SpecChain([
            Where.of(self.model.deleted_at.is_(None)),
            OrderBy.of(self.model.id.desc()),
            Paginate(page=page, page_size=page_size),
        ])

    async def get_activate_users(self, page: int, page_size: int):
        return await self.get_datas(spec=self._active_users_spec(page, page_size))

    async def filter_department_users(self, page: int, page_size: int, department):
        spec = SpecChain([
            *self._active_users_spec(page, page_size).specs,
            Where.of(self.model.department == department),
        ])

        return await self.get_datas(spec=spec)
