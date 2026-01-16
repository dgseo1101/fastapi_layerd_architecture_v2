from datetime import datetime
from typing import Optional

from core.domain.entities.entity import Entity

class CreateUserEntity(Entity):
    name: str
    email: str
    password_hash: str
    role: str

class UpdateUserEntity(Entity):
    name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    role: Optional[str] = None

class UserEntity(Entity):
    id: int
    name: str
    email: str
    password_hash: str
    role: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None