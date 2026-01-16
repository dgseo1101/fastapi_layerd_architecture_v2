from datetime import datetime
from typing import Optional

from core.application.dtos.base import BaseRequest, BaseResponse

class CreateUserRequestDto(BaseRequest):
    name: str
    email: str
    password_hash: str
    role: str

class UpdateUserRequestDto(BaseRequest):
    name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    role: Optional[str] = None

class UserResponseDto(BaseResponse):
    id: int
    name: str
    email: str
    password_hash: str
    role: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None