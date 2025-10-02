from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ProcessStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AnalyticsTimeWindow(str, Enum):
    HOUR = "1h"
    HOURS_8 = "8h"
    HOURS_12 = "12h"
    DAY = "1d"
    WEEK = "1w"


class PageMeta(BaseSchema):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(alias="pageSize", ge=1)
    pages: int = Field(ge=0)


class DocumentOut(BaseSchema):
    id: UUID = Field()
    name: str | None = Field(default=None)
    original_filename: str | None = Field(default=None, alias="originalFilename")
    content_type: str | None = Field(default=None, alias="contentType")
    file_size: int = Field(default=0, alias="fileSize")
    download_url: AnyUrl | None = Field(default=None, alias="downloadUrl")


class DocumentRead(BaseSchema):
    id: UUID = Field()
    name: str | None = Field(default=None)
    original_filename: str | None = Field(default=None, alias="originalFilename")
    content_type: str | None = Field(default=None, alias="contentType")
    file_size: int = Field(default=0, alias="fileSize")
    download_url: AnyUrl | None = Field(default=None, alias="downloadUrl")
    created_at: datetime = Field(alias="createdAt")


class DocumentSearchResponse(BaseSchema):
    items: list[DocumentRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class DocumentChunkRead(BaseSchema):
    id: UUID = Field()
    document_id: UUID = Field(alias="documentId")
    parent_id: UUID | None = Field(default=None, alias="parentId")
    content: str = Field()
    created_at: datetime = Field(alias="createdAt")


class DocumentChunkSearchResponse(BaseSchema):
    items: list[DocumentChunkRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class AgentOut(BaseSchema):
    id: UUID = Field()


class AgentRead(BaseSchema):
    id: UUID = Field()
    name: str = Field()
    description: str | None = Field(default=None)
    is_active: bool = Field(alias="isActive")
    is_default_recipient: bool = Field(alias="isDefaultRecipient")
    created_at: datetime = Field(alias="createdAt")


class AgentSearchResponse(BaseSchema):
    items: list[AgentRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class DocumentForwardedOut(BaseSchema):
    id: UUID = Field()


class ForwardedRead(BaseSchema):
    id: UUID = Field()
    document_id: UUID = Field(alias="documentId")
    sender_id: UUID | None = Field(default=None, alias="senderId")
    recipient_id: UUID = Field(alias="recipientId")
    route_id: UUID | None = Field(default=None, alias="routeId")
    purpose: str | None = Field(default=None)
    is_valid: bool | None = Field(default=None, alias="isValid")
    is_hidden: bool = Field(alias="isHidden")
    score: float | None = Field(default=None)
    created_at: datetime = Field(alias="createdAt")


class ForwardedSearchResponse(BaseSchema):
    items: list[ForwardedRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class DocumentForward(BaseSchema):
    sender_id: UUID = Field(alias="senderId")
    recipient_ids: list[UUID] = Field(alias="recipientIds")


class DocumentForwardsOut(BaseSchema):
    forwards: list[DocumentForward] = Field(default_factory=list)


class RouteRead(BaseSchema):
    id: UUID = Field()
    document_id: UUID = Field(alias="documentId")
    sender_id: UUID | None = Field(default=None, alias="senderId")
    status: ProcessStatus = Field()
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")


class RouteSearchResponse(BaseSchema):
    items: list[RouteRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class RouteDocumentOut(BaseSchema):
    id: UUID = Field()
    status: ProcessStatus = Field()
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")


class RouteForwardedOut(BaseSchema):
    sender_id: UUID | None = Field(default=None, alias="senderId")
    recipient_id: UUID | None = Field(default=None, alias="recipientId")
    score: float | None = Field(default=None)


class RouteInvestigationOut(BaseSchema):
    status: ProcessStatus = Field()
    forwards: list[RouteForwardedOut] = Field(default_factory=list)


class InventorySummaryOut(BaseSchema):
    documents_total: int = Field(alias="documentsTotal")
    agents_total: int = Field(alias="agentsTotal")
    routes_total: int = Field(alias="routesTotal")


class RoutesOverviewOut(BaseSchema):
    total: int = Field()
    pending: int = Field()
    in_progress: int = Field(alias="inProgress")
    completed: int = Field()
    failed: int = Field()
    timeout: int = Field()
    completed_last_24h: int = Field(alias="completedLast24H")
    average_completion_seconds: float | None = Field(default=None, alias="averageCompletionSeconds")
    completion_p95_seconds: float | None = Field(default=None, alias="completionP95Seconds")
    average_queue_seconds: float | None = Field(default=None, alias="averageQueueSeconds")
    queue_p95_seconds: float | None = Field(default=None, alias="queueP95Seconds")
    in_progress_average_age_seconds: float | None = Field(default=None, alias="inProgressAverageAgeSeconds")
    pending_average_age_seconds: float | None = Field(default=None, alias="pendingAverageAgeSeconds")
    failure_rate: float | None = Field(default=None, alias="failureRate")
    throughput_per_hour_last_24h: float | None = Field(default=None, alias="throughputPerHourLast24H")


class RouteBucketOut(BaseSchema):
    bucket_start: datetime = Field(alias="bucketStart")
    bucket_end: datetime = Field(alias="bucketEnd")
    total: int = Field()
    completed: int = Field()
    in_progress: int = Field(alias="inProgress")
    pending: int = Field()
    failed: int = Field()
    timeout: int = Field()
    average_completion_seconds: float | None = Field(default=None, alias="averageCompletionSeconds")
    average_queue_seconds: float | None = Field(default=None, alias="averageQueueSeconds")


class RoutesSummaryOut(BaseSchema):
    window: AnalyticsTimeWindow = Field()
    bucket_size_seconds: int = Field(alias="bucketSizeSeconds")
    bucket_limit: int = Field(alias="bucketLimit")
    overview: RoutesOverviewOut = Field()
    buckets: list[RouteBucketOut] = Field(default_factory=list)


class ForwardedRecipientDistributionResponse(BaseSchema):
    recipient_id: UUID | None = Field(default=None, alias="recipientId")
    recipient_name: str | None = Field(default=None, alias="recipientName")
    routes: int = Field()
    percentage: float = Field()


class ForwardedOverviewOut(BaseSchema):
    total_predictions: int = Field(alias="totalPredictions")
    manual_pending: int = Field(alias="manualPending")
    auto_approved: int = Field(alias="autoApproved")
    auto_rejected: int = Field(alias="autoRejected")
    routes_with_predictions: int = Field(alias="routesWithPredictions")
    routes_manual_pending: int = Field(alias="routesManualPending")
    routes_auto_resolved: int = Field(alias="routesAutoResolved")
    routes_with_rejections: int = Field(alias="routesWithRejections")
    average_predictions_per_route: float | None = Field(default=None, alias="averagePredictionsPerRoute")
    auto_resolution_ratio: float | None = Field(default=None, alias="autoResolutionRatio")
    auto_acceptance_rate: float | None = Field(default=None, alias="autoAcceptanceRate")
    manual_backlog_ratio: float | None = Field(default=None, alias="manualBacklogRatio")
    routes_coverage_ratio: float | None = Field(default=None, alias="routesCoverageRatio")
    rejection_ratio: float | None = Field(default=None, alias="rejectionRatio")
    distinct_recipients: int = Field(alias="distinctRecipients")
    distinct_senders: int = Field(alias="distinctSenders")
    average_score: float | None = Field(default=None, alias="averageScore")
    manual_average_score: float | None = Field(default=None, alias="manualAverageScore")
    accepted_average_score: float | None = Field(default=None, alias="acceptedAverageScore")
    rejected_average_score: float | None = Field(default=None, alias="rejectedAverageScore")
    first_forwarded_at: datetime | None = Field(default=None, alias="firstForwardedAt")
    last_forwarded_at: datetime | None = Field(default=None, alias="lastForwardedAt")
    routes_distribution: list[ForwardedRecipientDistributionResponse] = Field(
        default_factory=list, alias="routesDistribution"
    )


class ForwardedBucketOut(BaseSchema):
    bucket_start: datetime = Field(alias="bucketStart")
    bucket_end: datetime = Field(alias="bucketEnd")
    total: int = Field()
    manual_pending: int = Field(alias="manualPending")
    auto_approved: int = Field(alias="autoApproved")
    auto_rejected: int = Field(alias="autoRejected")
    average_score: float | None = Field(default=None, alias="averageScore")


class ForwardedSummaryOut(BaseSchema):
    window: AnalyticsTimeWindow = Field()
    bucket_size_seconds: int = Field(alias="bucketSizeSeconds")
    bucket_limit: int = Field(alias="bucketLimit")
    overview: ForwardedOverviewOut = Field()
    buckets: list[ForwardedBucketOut] = Field(default_factory=list)


class AnalyticsOverviewOut(BaseSchema):
    inventory: InventorySummaryOut = Field()
    routes: RoutesOverviewOut = Field()
    forwarded: ForwardedOverviewOut = Field()
