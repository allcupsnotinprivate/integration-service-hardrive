from fastapi import APIRouter, Depends

from ._dependencies import get_current_user
from ._schemas import JWTLoginForm, JWTRefreshForm, TokenSchema, UserSchema

router = APIRouter()


@router.post("/auth/login", response_model=TokenSchema, status_code=201)
async def login(form: JWTLoginForm = Depends()) -> TokenSchema:  # type: ignore[empty-body]
    pass


@router.post("/auth/logout", status_code=204)
async def logout(current_user: UserSchema = Depends(get_current_user)) -> None:
    pass


@router.get("/auth/me", response_model=UserSchema, status_code=200)
async def get_me(current_user: UserSchema = Depends(get_current_user)) -> UserSchema: ...  # type: ignore[empty-body]


@router.post("/auth/tokens/refresh", response_model=TokenSchema, status_code=201)
async def refresh_access_token(  # type: ignore[empty-body]
    form: JWTRefreshForm = Depends(), current_user: UserSchema = Depends(get_current_user)
) -> TokenSchema:
    pass
