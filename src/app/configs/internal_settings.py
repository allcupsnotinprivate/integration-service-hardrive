from pydantic import BaseModel, Field

from app.logs import LogLevel


class LogsSettings(BaseModel):
    enable: bool = Field(default=True)
    level: LogLevel = Field(default=LogLevel.INFO)


class AuthSettings(BaseModel):
    access_token_ttl: int = Field(default=30 * 60, ge=30)
    refresh_token_ttl: int = Field(default=7 * 24 * 60 * 60, ge=30)


class InternalSettings(BaseModel):
    log: LogsSettings = Field(default_factory=LogsSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
