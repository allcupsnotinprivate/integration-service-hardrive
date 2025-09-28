import uuid
from datetime import datetime
from typing import Literal

from fastapi import Form
from pydantic import EmailStr, Field

from app.infrastructure.router_service.http.schemas import AnalyticsTimeWindow, ProcessStatus
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
    sender_name: str | None = None
    route_status: ProcessStatus
    file_url: str | None = None  # Router service currently does not provide file download links
    document_name: str | None = None
    first_chunk_preview: str | None = None
    recipient_id: uuid.UUID | None = None
    recipient_name: str | None = None
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


class DocumentForwardingRequest(BaseAPISchema):
    purpose: str | None = Field(default=None)
    sender_id: uuid.UUID
    recipient_id: uuid.UUID


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


class ForwardingUpdateRequest(BaseAPISchema):
    purpose: str | None = Field(default=None)
    is_valid: bool | None = Field(default=None)
    is_hidden: bool | None = Field(default=None)


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
    status: ProcessStatus
    forwards: list[RouteForwardRecord]


class RouteInvestigationRequest(BaseAPISchema):
    allow_recovery: bool = Field(default=False, alias="allowRecovery")


# ----- Analytics -----


class AnalyticsInventorySummary(BaseAPISchema):
    documents_total: int
    agents_total: int
    routes_total: int


class AnalyticsRoutesOverview(BaseAPISchema):
    total: int
    pending: int
    in_progress: int
    completed: int
    failed: int
    timeout: int
    completed_last_24h: int
    average_completion_seconds: float | None = Field(default=None)
    completion_p95_seconds: float | None = Field(default=None)
    average_queue_seconds: float | None = Field(default=None)
    queue_p95_seconds: float | None = Field(default=None)
    in_progress_average_age_seconds: float | None = Field(default=None)
    pending_average_age_seconds: float | None = Field(default=None)
    failure_rate: float | None = Field(default=None)
    throughput_per_hour_last_24h: float | None = Field(default=None)


class AnalyticsRouteBucket(BaseAPISchema):
    bucket_start: datetime
    bucket_end: datetime
    total: int
    completed: int
    in_progress: int
    pending: int
    failed: int
    timeout: int
    average_completion_seconds: float | None = Field(default=None)
    average_queue_seconds: float | None = Field(default=None)


class AnalyticsRoutesSummary(BaseAPISchema):
    window: AnalyticsTimeWindow
    bucket_size_seconds: int
    bucket_limit: int
    overview: AnalyticsRoutesOverview
    buckets: list[AnalyticsRouteBucket]


class ForwardedRecipientDistributionResponse(BaseAPISchema):
    recipient_id: uuid.UUID | None = None
    recipient_name: str | None = None
    routes: int
    percentage: float


class AnalyticsForwardedOverview(BaseAPISchema):
    total_predictions: int
    manual_pending: int
    auto_approved: int
    auto_rejected: int
    routes_with_predictions: int
    routes_manual_pending: int
    routes_auto_resolved: int
    routes_with_rejections: int
    average_predictions_per_route: float | None = Field(default=None)
    auto_resolution_ratio: float | None = Field(default=None)
    auto_acceptance_rate: float | None = Field(default=None)
    manual_backlog_ratio: float | None = Field(default=None)
    routes_coverage_ratio: float | None = Field(default=None)
    rejection_ratio: float | None = Field(default=None)
    distinct_recipients: int
    distinct_senders: int
    average_score: float | None = Field(default=None)
    manual_average_score: float | None = Field(default=None)
    accepted_average_score: float | None = Field(default=None)
    rejected_average_score: float | None = Field(default=None)
    first_forwarded_at: datetime | None = Field(default=None)
    last_forwarded_at: datetime | None = Field(default=None)
    routes_distribution: list[ForwardedRecipientDistributionResponse] = Field(default_factory=list)


class AnalyticsForwardedBucket(BaseAPISchema):
    bucket_start: datetime
    bucket_end: datetime
    total: int
    manual_pending: int
    auto_approved: int
    auto_rejected: int
    average_score: float | None = Field(default=None)


class AnalyticsForwardedSummary(BaseAPISchema):
    window: AnalyticsTimeWindow
    bucket_size_seconds: int
    bucket_limit: int
    overview: AnalyticsForwardedOverview
    buckets: list[AnalyticsForwardedBucket]


class AnalyticsOverview(BaseAPISchema):
    inventory: AnalyticsInventorySummary
    routes: AnalyticsRoutesOverview
    forwarded: AnalyticsForwardedOverview
