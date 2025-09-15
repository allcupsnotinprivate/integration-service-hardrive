import uuid
from datetime import datetime
from typing import Literal

from fastapi import Form
from pydantic import EmailStr, Field

from app.infrastructure.router_service.http.schemas import ProcessStatus
from app.models import UserRole
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
    role: UserRole


# ----- Users -----


class UserIn(BaseAPISchema):
    username: str
    email: EmailStr
    fullname: str | None = Field(default=None)
    is_active: bool
    role: UserRole
    password: str


class UserOut(BaseAPISchema):
    id: uuid.UUID
    created_at: datetime
    username: str
    email: EmailStr
    fullname: str | None
    is_active: bool
    role: UserRole


# ----- Agents -----


class AgentRegisterRequest(BaseAPISchema):
    name: str = Field(..., min_length=1)
    description: str | None = None
    is_default_recipient: bool = False


class AgentCreatedResponse(BaseAPISchema):
    id: uuid.UUID


class AgentRecord(BaseAPISchema):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    is_default_recipient: bool
    created_at: datetime


# ----- Documents ------


class ManualDocumentRequest(BaseAPISchema):
    name: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class DocumentCreatedResponse(BaseAPISchema):
    id: uuid.UUID


class DocumentSummary(BaseAPISchema):
    id: uuid.UUID
    name: str | None = None
    created_at: datetime


class DocumentHistoryItem(BaseAPISchema):
    document_id: uuid.UUID
    route_id: uuid.UUID
    document_created_at: datetime | None = None
    route_created_at: datetime
    sender_id: uuid.UUID | None = None
    route_status: ProcessStatus
    file_url: str | None = None  # Router service currently does not provide file download links
    document_name: str | None = None
    first_chunk_preview: str | None = None
    predicted_recipient_id: uuid.UUID | None = None
    prediction_confidence: float | None = None
    investigation_duration_seconds: float | None = None


# ----- Forwarding -----


class ForwardDocumentRequest(BaseAPISchema):
    purpose: str | None = Field(default=None)
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    document_id: uuid.UUID


class ForwardCreatedResponse(BaseAPISchema):
    id: uuid.UUID


class ForwardingRecord(BaseAPISchema):
    id: uuid.UUID
    document_id: uuid.UUID
    sender_id: uuid.UUID | None
    recipient_id: uuid.UUID
    route_id: uuid.UUID | None
    purpose: str | None
    is_valid: bool | None
    is_hidden: bool
    score: float | None
    created_at: datetime


# ----- Routes -----


class RouteRecord(BaseAPISchema):
    id: uuid.UUID
    document_id: uuid.UUID
    sender_id: uuid.UUID | None
    status: ProcessStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class RouteDetails(BaseAPISchema):
    id: uuid.UUID
    status: ProcessStatus
    started_at: datetime | None
    completed_at: datetime | None


class RouteForwardRecord(BaseAPISchema):
    sender_id: uuid.UUID | None
    recipient_id: uuid.UUID | None
    score: float | None


class RouteInvestigationRecord(BaseAPISchema):
    forwards: list[RouteForwardRecord]


class RouteInvestigationRequest(BaseAPISchema):
    allow_recovery: bool = Field(default=False, alias="allowRecovery")
