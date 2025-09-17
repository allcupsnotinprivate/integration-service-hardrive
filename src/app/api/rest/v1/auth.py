from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.service_layer import A_AuthService

from ._dependencies import get_current_user, security
from ._schemas import JWTLoginForm, JWTRefreshForm, TokenSchema, UserSchema

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=TokenSchema,
    status_code=201,
    description=(
        "В поле `username` необходимо передавать `email` пользователя; авторизация по отдельному `username` не поддерживается."
    ),
)
@inject
async def login(
    form: JWTLoginForm = Depends(),
    auth_service: Injected[A_AuthService] = Depends(),
) -> TokenSchema:
    tokens = await auth_service.authenticate(form.username, form.password)
    return TokenSchema(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/auth/logout", status_code=204)
@inject
async def logout(
    current_user: UserSchema = Depends(get_current_user),
    auth_service: Injected[A_AuthService] = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    await auth_service.logout(credentials.credentials)


@router.get("/auth/me", response_model=UserSchema, status_code=200)
@inject
async def get_me(current_user: UserSchema = Depends(get_current_user)) -> UserSchema:
    return current_user


@router.post("/auth/tokens/refresh", response_model=TokenSchema, status_code=201)
@inject
async def refresh_access_token(
    form: JWTRefreshForm = Depends(),
    current_user: UserSchema = Depends(get_current_user),
    auth_service: Injected[A_AuthService] = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenSchema:
    tokens = await auth_service.refresh_tokens(credentials.credentials, form.refresh_token)
    return TokenSchema(access_token=tokens.access_token, refresh_token=tokens.refresh_token)
