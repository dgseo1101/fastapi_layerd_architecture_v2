from dependency_injector.wiring import Provide, inject
from typing import List
from fastapi import APIRouter, Depends, Query

from core.application.dtos.user_dto import (
    CreateUserRequestDto,
    UpdateUserRequestDto,
    UserResponseDto,
)
from server.application.services.user_service import UserService
from server.infrastructure.di.container import ServerContainer

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponseDto)
@inject
async def create_user(
    dto: CreateUserRequestDto,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return await user_service.create(dto=dto)


@router.get("/", response_model=List[UserResponseDto])
@inject
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return await user_service.get_users(page=page, page_size=page_size)


@router.get("/activate-user", response_model=List[UserResponseDto])
@inject
async def get_active_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return await user_service.get_active_users(page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserResponseDto)
@inject
async def get_user(
    user_id: int,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return await user_service.get_by_id(obj_id=user_id)


@router.put("/{user_id}", response_model=UserResponseDto)
@inject
async def update_user(
    user_id: int,
    dto: UpdateUserRequestDto,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return await user_service.update_by_id(obj_id=user_id, dto=dto)


@router.delete("/{user_id}")
@inject
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(Provide[ServerContainer.user_service]),
):
    return await user_service.delete_by_id(obj_id=user_id)
