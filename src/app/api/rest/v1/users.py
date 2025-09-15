import uuid

from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, Path

from app.service_layer import AUsersService

from ._dependencies import get_current_user
from ._schemas import UserIn, UserOut, UserSchema

router = APIRouter()


@router.post("/users", response_model=UserOut, status_code=201)
@inject
async def create_user(
    data: UserIn,
    users_service: Injected[AUsersService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> UserOut:
    user = await users_service.create_user(
        username=data.username,
        email=data.email,
        fullname=data.fullname,
        is_active=data.is_active,
        role=data.role,
        password=data.password,
    )
    return UserOut(
        id=user.id,
        created_at=user.created_at,
        username=user.username,
        email=user.email,
        fullname=user.fullname,
        is_active=user.is_active,
        role=user.role,
    )


@router.get("/users/{userId}", response_model=UserOut, status_code=200)
@inject
async def get_user(
    user_id: uuid.UUID = Path(alias="userId"),
    users_service: Injected[AUsersService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> UserOut:
    user = await users_service.get_user(user_id)
    return UserOut(
        id=user.id,
        created_at=user.created_at,
        username=user.username,
        email=user.email,
        fullname=user.fullname,
        is_active=user.is_active,
        role=user.role,
    )
