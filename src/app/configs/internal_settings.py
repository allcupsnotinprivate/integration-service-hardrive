from pydantic import BaseModel, EmailStr, Field, field_validator

from app.logs import LogLevel
from app.models import UserRole


class LogsSettings(BaseModel):
    enable: bool = Field(default=True)
    level: LogLevel = Field(default=LogLevel.INFO)


class BootstrapUserSettings(BaseModel):
    username: str = Field(default="system")
    email: EmailStr = Field(default="system@digitalsec.local")
    fullname: str | None = Field(default=None)
    password: str = Field(default="digitalsec_password")
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.SYSTEM)

    @field_validator("username")
    def _validate_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            msg = "Bootstrap username must not be empty"
            raise ValueError(msg)
        return username

    @field_validator("password")
    def _validate_password(cls, value: str) -> str:
        if not value:
            msg = "Bootstrap password must not be empty"
            raise ValueError(msg)
        return value


class BootstrapSettings(BaseModel):
    enabled: bool = Field(default=True)
    user: BootstrapUserSettings = Field(default_factory=BootstrapUserSettings)


class AuthSettings(BaseModel):
    access_token_ttl: int = Field(default=30 * 60, ge=30)
    refresh_token_ttl: int = Field(default=7 * 24 * 60 * 60, ge=30)


class InternalSettings(BaseModel):
    log: LogsSettings = Field(default_factory=LogsSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    bootstrap: BootstrapSettings = Field(default_factory=BootstrapSettings)
