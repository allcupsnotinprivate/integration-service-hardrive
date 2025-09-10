from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ._schemas import UserSchema

security = HTTPBearer()


async def get_current_user(  # type: ignore[empty-body]
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserSchema:
    pass
