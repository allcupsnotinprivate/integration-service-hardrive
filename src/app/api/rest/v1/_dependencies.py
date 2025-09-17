from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.service_layer import A_AuthService

from ._schemas import UserSchema

security = HTTPBearer()


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: Injected[A_AuthService] = Depends(),
) -> UserSchema:
    user = await auth_service.get_user_by_access_token(credentials.credentials)

    return UserSchema(
        id=user.id,
        created_at=user.created_at,
        username=user.username,
        email=user.email,
        fullname=user.fullname,
        is_active=user.is_active,
        role=user.role,
    )
