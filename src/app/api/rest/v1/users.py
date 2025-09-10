import uuid

from fastapi import APIRouter, Body, Depends, Path, Query

from app.utils.schemas import PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import UserIn, UserOut, UserSchema, UserUpdate

router = APIRouter()


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(data: UserIn, current_user: UserSchema = Depends(get_current_user)) -> UserOut:  # type: ignore[empty-body]
    pass


@router.get("/users", response_model=PaginatedResponse[UserOut], status_code=200)
async def search_users(  # type: ignore[empty-body]
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[UserOut]:
    pass


@router.get("/users/{userId}", response_model=UserOut, status_code=200)
async def get_user(  # type: ignore[empty-body]
    user_id: uuid.UUID = Path(alias="userId"), current_user: UserSchema = Depends(get_current_user)
) -> UserOut:
    pass


@router.delete("/users/{userId}", status_code=204)
async def delete_user(
    user_id: uuid.UUID = Path(alias="userId"), current_user: UserSchema = Depends(get_current_user)
) -> None:
    pass


@router.patch("/users/{userId}", response_model=UserOut, status_code=200)
async def edit_user(  # type: ignore[empty-body]
    user_id: uuid.UUID = Path(alias="userId"),
    data: UserUpdate = Body(),
    current_user: UserSchema = Depends(get_current_user),
) -> UserOut:
    pass
