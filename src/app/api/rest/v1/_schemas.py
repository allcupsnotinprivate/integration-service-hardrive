import uuid
from datetime import datetime
from typing import Literal

from fastapi import Form
from pydantic import EmailStr, Field

from app.utils.schemas import BaseAPISchema

# ----- External and Base Schemas -----


class ProviderInfoIn(BaseAPISchema):
    provider: str = Field()
    source_id: str = Field()
    metadata: dict[str, str] | None = Field(default=None)


class ProviderInfoOut(BaseAPISchema):
    provider: str = Field()
    source_id: str = Field()
    synced_at: datetime | None = Field(default=None)
    metadata: dict[str, str] | None = Field(default=None)


# ----- Auth -----


class JWTLoginForm:
    def __init__(
        self,
        username: str = Form(
            description="The username of the user trying to authenticate.",
        ),
        password: str = Form(
            description="The password of the user trying to authenticate.",
        ),
    ):
        self.username = username
        self.password = password


class JWTRefreshForm:
    def __init__(
        self,
        refresh_token: str = Form(description="Refresh token to generate a new access token."),
    ):
        self.refresh_token = refresh_token


class TokenData(BaseAPISchema):
    sub: str
    exp: int
    iat: int


class TokenSchema(BaseAPISchema):
    access_token: str = Field(...)
    refresh_token: str | None = Field(default=None)
    token_type: Literal["bearer"] = Field(default="bearer")


class UserSchema(BaseAPISchema):
    id: uuid.UUID
    created_at: datetime
    username: str
    email: EmailStr
    fullname: str | None = Field(default=None)
    is_active: bool
    role: Literal["system", "operator"]


# ----- Users -----


class UserIn(BaseAPISchema):
    username: str
    email: EmailStr
    fullname: str | None = Field(default=None)
    is_active: bool
    role: Literal["system", "operator"]


class UserOut(BaseAPISchema):
    id: uuid.UUID
    created_at: datetime
    username: str
    email: EmailStr
    fullname: str | None
    is_active: bool
    role: Literal["system", "operator"]


class UserUpdate(BaseAPISchema):
    username: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    fullname: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    role: Literal["system", "operator"] = Field(default="operator")
