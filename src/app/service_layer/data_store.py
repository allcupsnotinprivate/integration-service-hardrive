import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any, Generic, NoReturn, TypeVar
from uuid import UUID

import httpx

from app import exceptions
from app.infrastructure import ARouterServiceHTTPClient
from app.infrastructure.router_service.http.schemas import AnalyticsTimeWindow, ProcessStatus

from .aClasses import AService

T = TypeVar("T")


@dataclass(slots=True)
class Pagination:
    page: int
    per_page: int
    total: int
    total_pages: int


@dataclass(slots=True)
class PaginatedResult(Generic[T]):
    items: list[T]
    meta: Pagination


@dataclass(slots=True)
class AgentData:
    id: UUID
    name: str
    description: str | None
    is_active: bool
    is_default_recipient: bool
    created_at: datetime


@dataclass(slots=True)
class DocumentSummaryData:
    id: UUID
    name: str | None
    created_at: datetime


@dataclass(slots=True)
class DocumentHistoryRecord:
    document_id: UUID
    route_id: UUID
    document_created_at: datetime | None
    route_created_at: datetime
    sender_id: UUID | None
    route_status: ProcessStatus
    investigation_status: ProcessStatus | None
    document_name: str | None
    first_chunk_preview: str | None
    predicted_sender_id: UUID | None
    predicted_recipient_id: UUID | None
    prediction_confidence: float | None
    investigation_duration_seconds: float | None
    manual_review_available: bool


@dataclass(slots=True)
class ForwardingRecordData:
    id: UUID
    document_id: UUID
    sender_id: UUID | None
    recipient_id: UUID
    route_id: UUID | None
    purpose: str | None
    is_valid: bool | None
    is_hidden: bool
    score: float | None
    created_at: datetime


@dataclass(slots=True)
class RouteRecordData:
    id: UUID
    document_id: UUID
    sender_id: UUID | None
    status: ProcessStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


@dataclass(slots=True)
class RouteDetailsData:
    id: UUID
    status: ProcessStatus
    started_at: datetime | None
    completed_at: datetime | None


@dataclass(slots=True)
class RouteInvestigationForwardData:
    sender_id: UUID | None
    recipient_id: UUID | None
    score: float | None


@dataclass(slots=True)
class RouteInvestigationData:
    status: ProcessStatus
    forwards: list[RouteInvestigationForwardData]


@dataclass(slots=True)
class InventorySummaryData:
    documents_total: int
    agents_total: int
    routes_total: int


@dataclass(slots=True)
class RoutesOverviewData:
    total: int
    pending: int
    in_progress: int
    completed: int
    failed: int
    timeout: int
    completed_last_24h: int
    average_completion_seconds: float | None
    completion_p95_seconds: float | None
    average_queue_seconds: float | None
    queue_p95_seconds: float | None
    in_progress_average_age_seconds: float | None
    pending_average_age_seconds: float | None
    failure_rate: float | None
    throughput_per_hour_last_24h: float | None


@dataclass(slots=True)
class RouteBucketData:
    bucket_start: datetime
    bucket_end: datetime
    total: int
    completed: int
    in_progress: int
    pending: int
    failed: int
    timeout: int
    average_completion_seconds: float | None
    average_queue_seconds: float | None


@dataclass(slots=True)
class RoutesSummaryData:
    window: AnalyticsTimeWindow
    bucket_size_seconds: int
    bucket_limit: int
    overview: RoutesOverviewData
    buckets: list[RouteBucketData]


@dataclass(slots=True)
class ForwardedOverviewData:
    total_predictions: int
    manual_pending: int
    auto_approved: int
    auto_rejected: int
    routes_with_predictions: int
    routes_manual_pending: int
    routes_auto_resolved: int
    routes_with_rejections: int
    average_predictions_per_route: float | None
    auto_resolution_ratio: float | None
    auto_acceptance_rate: float | None
    manual_backlog_ratio: float | None
    routes_coverage_ratio: float | None
    distinct_recipients: int
    distinct_senders: int
    average_score: float | None
    manual_average_score: float | None
    accepted_average_score: float | None
    rejected_average_score: float | None
    first_forwarded_at: datetime | None
    last_forwarded_at: datetime | None


@dataclass(slots=True)
class ForwardedBucketData:
    bucket_start: datetime
    bucket_end: datetime
    total: int
    manual_pending: int
    auto_approved: int
    auto_rejected: int
    average_score: float | None


@dataclass(slots=True)
class ForwardedSummaryData:
    window: AnalyticsTimeWindow
    bucket_size_seconds: int
    bucket_limit: int
    overview: ForwardedOverviewData
    buckets: list[ForwardedBucketData]


@dataclass(slots=True)
class AnalyticsOverviewData:
    inventory: InventorySummaryData
    routes: RoutesOverviewData
    forwarded: ForwardedOverviewData


class ADataStoreService(AService, abc.ABC):
    @abc.abstractmethod
    async def list_agents(
        self,
        *,
        page: int,
        per_page: int,
        name: str | None,
        description: str | None,
        is_active: bool | None,
        is_default_recipient: bool | None,
    ) -> PaginatedResult[AgentData]:
        raise NotImplementedError

    @abc.abstractmethod
    async def register_agent(
        self,
        *,
        name: str,
        description: str | None,
        is_default_recipient: bool,
    ) -> UUID:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_documents(
        self,
        *,
        page: int,
        per_page: int,
        name: str | None,
        created_from: datetime | None,
        created_to: datetime | None,
    ) -> PaginatedResult[DocumentSummaryData]:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_manual_document(self, *, name: str, content: str) -> UUID:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_document_history(
        self,
        *,
        page: int,
        per_page: int,
        document_id: UUID | None,
        sender_id: UUID | None,
        status_filter: ProcessStatus | None,
        started_from: datetime | None,
        started_to: datetime | None,
        completed_from: datetime | None,
        completed_to: datetime | None,
    ) -> PaginatedResult[DocumentHistoryRecord]:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_forwardings(
        self,
        *,
        page: int,
        per_page: int,
        document_id: UUID | None,
        sender_id: UUID | None,
        recipient_id: UUID | None,
        route_id: UUID | None,
        is_valid: bool | None,
        is_hidden: bool | None,
        purpose: str | None,
    ) -> PaginatedResult[ForwardingRecordData]:
        raise NotImplementedError

    @abc.abstractmethod
    async def forward_document(
        self,
        *,
        purpose: str | None,
        sender_id: UUID,
        recipient_id: UUID,
        document_id: UUID,
    ) -> UUID:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_forwarding(
        self,
        *,
        forward_id: UUID,
        purpose: str | None,
        is_valid: bool | None,
        is_hidden: bool | None,
    ) -> ForwardingRecordData:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_routes(
        self,
        *,
        page: int,
        per_page: int,
        document_id: UUID | None,
        sender_id: UUID | None,
        status_filter: ProcessStatus | None,
        started_from: datetime | None,
        started_to: datetime | None,
        completed_from: datetime | None,
        completed_to: datetime | None,
    ) -> PaginatedResult[RouteRecordData]:
        raise NotImplementedError

    @abc.abstractmethod
    async def retrieve_route(self, *, route_id: UUID) -> RouteDetailsData:
        raise NotImplementedError

    @abc.abstractmethod
    async def cancel_route(self, *, route_id: UUID) -> RouteDetailsData:
        raise NotImplementedError

    @abc.abstractmethod
    async def trigger_manual_investigation(self, *, route_id: UUID, allow_recovery: bool) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_route_investigation(self, *, route_id: UUID) -> RouteInvestigationData:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_analytics_overview(self) -> AnalyticsOverviewData:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_routes_summary(
        self,
        *,
        window: AnalyticsTimeWindow,
        bucket_limit: int | None = None,
    ) -> RoutesSummaryData:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_forwarded_summary(
        self,
        *,
        window: AnalyticsTimeWindow,
        bucket_limit: int | None = None,
    ) -> ForwardedSummaryData:
        raise NotImplementedError


class DataStoreService(ADataStoreService):
    def __init__(self, client: ARouterServiceHTTPClient):
        self._client = client

    async def list_agents(
        self,
        *,
        page: int,
        per_page: int,
        name: str | None,
        description: str | None,
        is_active: bool | None,
        is_default_recipient: bool | None,
    ) -> PaginatedResult[AgentData]:
        try:
            response = await self._client.search_agents(
                page=page,
                page_size=per_page,
                name=name,
                description=description,
                is_active=is_active,
                is_default_recipient=is_default_recipient,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch agents")

        items = [
            AgentData(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                is_active=agent.is_active,
                is_default_recipient=agent.is_default_recipient,
                created_at=agent.created_at,
            )
            for agent in response.items
        ]
        meta = Pagination(
            page=response.page_info.page,
            per_page=response.page_info.page_size,
            total=response.page_info.total,
            total_pages=response.page_info.pages,
        )
        return PaginatedResult(items=items, meta=meta)

    async def register_agent(
        self,
        *,
        name: str,
        description: str | None,
        is_default_recipient: bool,
    ) -> UUID:
        normalized_name = name.strip()
        if not normalized_name:
            raise exceptions.ValidationError("Agent name must not be empty")
        try:
            result = await self._client.register_agent(
                name=normalized_name,
                description=description,
                is_default_recipient=is_default_recipient,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to register agent")
        return result.id

    async def search_documents(
        self,
        *,
        page: int,
        per_page: int,
        name: str | None,
        created_from: datetime | None,
        created_to: datetime | None,
    ) -> PaginatedResult[DocumentSummaryData]:
        try:
            response = await self._client.search_documents(
                page=page,
                page_size=per_page,
                name=name,
                created_from=created_from,
                created_to=created_to,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch documents")

        items = [
            DocumentSummaryData(id=document.id, name=document.name, created_at=document.created_at)
            for document in response.items
        ]
        meta = Pagination(
            page=response.page_info.page,
            per_page=response.page_info.page_size,
            total=response.page_info.total,
            total_pages=response.page_info.pages,
        )
        return PaginatedResult(items=items, meta=meta)

    async def create_manual_document(self, *, name: str, content: str) -> UUID:
        normalized_name = name.strip()
        normalized_content = content.strip()
        if not normalized_name or not normalized_content:
            raise exceptions.ValidationError("Name and content must not be empty")
        try:
            response = await self._client.admit_document(name=normalized_name, content=normalized_content)
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to create document")
        return response.id

    async def get_document_history(
        self,
        *,
        page: int,
        per_page: int,
        document_id: UUID | None,
        sender_id: UUID | None,
        status_filter: ProcessStatus | None,
        started_from: datetime | None,
        started_to: datetime | None,
        completed_from: datetime | None,
        completed_to: datetime | None,
    ) -> PaginatedResult[DocumentHistoryRecord]:
        try:
            routes_response = await self._client.search_routes(
                page=page,
                page_size=per_page,
                document_id=document_id,
                sender_id=sender_id,
                status=status_filter,
                started_from=started_from,
                started_to=started_to,
                completed_from=completed_from,
                completed_to=completed_to,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch document history")

        items: list[DocumentHistoryRecord] = []
        for route in routes_response.items:
            first_chunk_preview: str | None = None
            try:
                chunks_response = await self._client.search_document_chunks(
                    page=1,
                    page_size=1,
                    document_id=route.document_id,
                )
                if chunks_response.items:
                    first_chunk_preview = chunks_response.items[0].content
            except httpx.HTTPError:
                first_chunk_preview = None

            investigation_status: ProcessStatus | None = None
            predicted_sender_id: UUID | None = None
            predicted_recipient_id: UUID | None = None
            prediction_confidence: float | None = None
            try:
                investigation = await self._client.retrieve_investigation_results(route_id=route.id)
                investigation_status = investigation.status
                if investigation.forwards:
                    last_forward = investigation.forwards[-1]
                    predicted_sender_id = last_forward.sender_id
                    predicted_recipient_id = last_forward.recipient_id
                    prediction_confidence = last_forward.score
            except httpx.HTTPError:
                investigation_status = None

            duration = None
            if route.started_at:
                end_time = route.completed_at or datetime.now(timezone.utc)
                duration = max((end_time - route.started_at).total_seconds(), 0.0)

            document_created_at = route.created_at

            # TODO: add document data for fields `document_created_at`, `document_name`
            items.append(
                DocumentHistoryRecord(
                    document_id=route.document_id,
                    route_id=route.id,
                    document_created_at=document_created_at,
                    route_created_at=route.created_at,
                    sender_id=route.sender_id,
                    route_status=route.status,
                    investigation_status=investigation_status,
                    document_name=None,
                    first_chunk_preview=first_chunk_preview,
                    predicted_sender_id=predicted_sender_id,
                    predicted_recipient_id=predicted_recipient_id,
                    prediction_confidence=prediction_confidence,
                    investigation_duration_seconds=duration,
                    manual_review_available=route.status
                    not in {
                        ProcessStatus.COMPLETED,
                        ProcessStatus.CANCELLED,
                    },
                )
            )

        meta = Pagination(
            page=routes_response.page_info.page,
            per_page=routes_response.page_info.page_size,
            total=routes_response.page_info.total,
            total_pages=routes_response.page_info.pages,
        )
        return PaginatedResult(items=items, meta=meta)

    async def list_forwardings(
        self,
        *,
        page: int,
        per_page: int,
        document_id: UUID | None,
        sender_id: UUID | None,
        recipient_id: UUID | None,
        route_id: UUID | None,
        is_valid: bool | None,
        is_hidden: bool | None,
        purpose: str | None,
    ) -> PaginatedResult[ForwardingRecordData]:
        try:
            response = await self._client.search_forwarded(
                page=page,
                page_size=per_page,
                document_id=document_id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                route_id=route_id,
                is_valid=is_valid,
                is_hidden=is_hidden,
                purpose=purpose,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch forwardings")

        items = [
            ForwardingRecordData(
                id=forward.id,
                document_id=forward.document_id,
                sender_id=forward.sender_id,
                recipient_id=forward.recipient_id,
                route_id=forward.route_id,
                purpose=forward.purpose,
                is_valid=forward.is_valid,
                is_hidden=forward.is_hidden,
                score=forward.score,
                created_at=forward.created_at,
            )
            for forward in response.items
        ]
        meta = Pagination(
            page=response.page_info.page,
            per_page=response.page_info.page_size,
            total=response.page_info.total,
            total_pages=response.page_info.pages,
        )
        return PaginatedResult(items=items, meta=meta)

    async def forward_document(
        self,
        *,
        purpose: str | None,
        sender_id: UUID,
        recipient_id: UUID,
        document_id: UUID,
    ) -> UUID:
        try:
            response = await self._client.forward_document(
                purpose=purpose,
                sender_id=sender_id,
                recipient_id=recipient_id,
                document_id=document_id,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to forward document")
        return response.id

    async def update_forwarding(
        self,
        *,
        forward_id: UUID,
        purpose: str | None,
        is_valid: bool | None,
        is_hidden: bool | None,
    ) -> ForwardingRecordData:
        if purpose is None and is_valid is None and is_hidden is None:
            raise exceptions.ValidationError("No fields provided for update")

        try:
            result = await self._client.update_forwarded(
                forward_id=forward_id,
                purpose=purpose,
                is_valid=is_valid,
                is_hidden=is_hidden,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to update forwarding")

        return ForwardingRecordData(
            id=result.id,
            document_id=result.document_id,
            sender_id=result.sender_id,
            recipient_id=result.recipient_id,
            route_id=result.route_id,
            purpose=result.purpose,
            is_valid=result.is_valid,
            is_hidden=result.is_hidden,
            score=result.score,
            created_at=result.created_at,
        )

    async def list_routes(
        self,
        *,
        page: int,
        per_page: int,
        document_id: UUID | None,
        sender_id: UUID | None,
        status_filter: ProcessStatus | None,
        started_from: datetime | None,
        started_to: datetime | None,
        completed_from: datetime | None,
        completed_to: datetime | None,
    ) -> PaginatedResult[RouteRecordData]:
        try:
            response = await self._client.search_routes(
                page=page,
                page_size=per_page,
                document_id=document_id,
                sender_id=sender_id,
                status=status_filter,
                started_from=started_from,
                started_to=started_to,
                completed_from=completed_from,
                completed_to=completed_to,
            )
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch routes")

        items = [
            RouteRecordData(
                id=route.id,
                document_id=route.document_id,
                sender_id=route.sender_id,
                status=route.status,
                started_at=route.started_at,
                completed_at=route.completed_at,
                created_at=route.created_at,
            )
            for route in response.items
        ]
        meta = Pagination(
            page=response.page_info.page,
            per_page=response.page_info.page_size,
            total=response.page_info.total,
            total_pages=response.page_info.pages,
        )
        return PaginatedResult(items=items, meta=meta)

    async def retrieve_route(self, *, route_id: UUID) -> RouteDetailsData:
        try:
            route = await self._client.retrieve_route(route_id=route_id)
        except httpx.HTTPError as exc:
            self._handle_http_error(
                exc, "Route not found" if isinstance(exc, httpx.HTTPStatusError) else "Unable to retrieve route"
            )

        return RouteDetailsData(
            id=route.id,
            status=route.status,
            started_at=route.started_at,
            completed_at=route.completed_at,
        )

    async def cancel_route(self, *, route_id: UUID) -> RouteDetailsData:
        try:
            route = await self._client.cancel_route(route_id=route_id)
        except httpx.HTTPError as exc:
            self._handle_http_error(
                exc, "Route not found" if isinstance(exc, httpx.HTTPStatusError) else "Unable to cancel route"
            )

        return RouteDetailsData(
            id=route.id,
            status=route.status,
            started_at=route.started_at,
            completed_at=route.completed_at,
        )

    async def trigger_manual_investigation(self, *, route_id: UUID, allow_recovery: bool) -> None:
        try:
            await self._client.investigate_routing(route_id=route_id, allow_recovery=allow_recovery)
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to trigger investigation")

    async def get_route_investigation(self, *, route_id: UUID) -> RouteInvestigationData:
        try:
            result = await self._client.retrieve_investigation_results(route_id=route_id)
        except httpx.HTTPError as exc:
            self._handle_http_error(
                exc,
                "Investigation not found"
                if isinstance(exc, httpx.HTTPStatusError)
                else "Unable to fetch investigation results",
            )

        forwards = [
            RouteInvestigationForwardData(
                sender_id=forward.sender_id,
                recipient_id=forward.recipient_id,
                score=forward.score,
            )
            for forward in result.forwards
        ]
        return RouteInvestigationData(status=result.status, forwards=forwards)

    async def get_analytics_overview(self) -> AnalyticsOverviewData:
        try:
            result = await self._client.get_analytics_overview()
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch analytics overview")

        inventory = InventorySummaryData(
            documents_total=result.inventory.documents_total,
            agents_total=result.inventory.agents_total,
            routes_total=result.inventory.routes_total,
        )
        routes_overview = self._map_routes_overview(result.routes)
        forwarded_overview = self._map_forwarded_overview(result.forwarded)
        return AnalyticsOverviewData(
            inventory=inventory,
            routes=routes_overview,
            forwarded=forwarded_overview,
        )

    async def get_routes_summary(
        self,
        *,
        window: AnalyticsTimeWindow,
        bucket_limit: int | None = None,
    ) -> RoutesSummaryData:
        try:
            result = await self._client.get_routes_summary(window=window, bucket_limit=bucket_limit)
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch routes analytics summary")

        overview = self._map_routes_overview(result.overview)
        buckets = [self._map_route_bucket(bucket) for bucket in result.buckets]
        return RoutesSummaryData(
            window=result.window,
            bucket_size_seconds=result.bucket_size_seconds,
            bucket_limit=result.bucket_limit,
            overview=overview,
            buckets=buckets,
        )

    async def get_forwarded_summary(
        self,
        *,
        window: AnalyticsTimeWindow,
        bucket_limit: int | None = None,
    ) -> ForwardedSummaryData:
        try:
            result = await self._client.get_forwarded_summary(window=window, bucket_limit=bucket_limit)
        except httpx.HTTPError as exc:
            self._handle_http_error(exc, "Unable to fetch forwarding analytics summary")

        overview = self._map_forwarded_overview(result.overview)
        buckets = [self._map_forwarded_bucket(bucket) for bucket in result.buckets]
        return ForwardedSummaryData(
            window=result.window,
            bucket_size_seconds=result.bucket_size_seconds,
            bucket_limit=result.bucket_limit,
            overview=overview,
            buckets=buckets,
        )

    def _map_routes_overview(self, overview: Any) -> RoutesOverviewData:
        return RoutesOverviewData(
            total=overview.total,
            pending=overview.pending,
            in_progress=overview.in_progress,
            completed=overview.completed,
            failed=overview.failed,
            timeout=overview.timeout,
            completed_last_24h=overview.completed_last_24h,
            average_completion_seconds=overview.average_completion_seconds,
            completion_p95_seconds=overview.completion_p95_seconds,
            average_queue_seconds=overview.average_queue_seconds,
            queue_p95_seconds=overview.queue_p95_seconds,
            in_progress_average_age_seconds=overview.in_progress_average_age_seconds,
            pending_average_age_seconds=overview.pending_average_age_seconds,
            failure_rate=overview.failure_rate,
            throughput_per_hour_last_24h=overview.throughput_per_hour_last_24h,
        )

    def _map_route_bucket(self, bucket: Any) -> RouteBucketData:
        return RouteBucketData(
            bucket_start=bucket.bucket_start,
            bucket_end=bucket.bucket_end,
            total=bucket.total,
            completed=bucket.completed,
            in_progress=bucket.in_progress,
            pending=bucket.pending,
            failed=bucket.failed,
            timeout=bucket.timeout,
            average_completion_seconds=bucket.average_completion_seconds,
            average_queue_seconds=bucket.average_queue_seconds,
        )

    def _map_forwarded_overview(self, overview: Any) -> ForwardedOverviewData:
        return ForwardedOverviewData(
            total_predictions=overview.total_predictions,
            manual_pending=overview.manual_pending,
            auto_approved=overview.auto_approved,
            auto_rejected=overview.auto_rejected,
            routes_with_predictions=overview.routes_with_predictions,
            routes_manual_pending=overview.routes_manual_pending,
            routes_auto_resolved=overview.routes_auto_resolved,
            routes_with_rejections=overview.routes_with_rejections,
            average_predictions_per_route=overview.average_predictions_per_route,
            auto_resolution_ratio=overview.auto_resolution_ratio,
            auto_acceptance_rate=overview.auto_acceptance_rate,
            manual_backlog_ratio=overview.manual_backlog_ratio,
            routes_coverage_ratio=overview.routes_coverage_ratio,
            distinct_recipients=overview.distinct_recipients,
            distinct_senders=overview.distinct_senders,
            average_score=overview.average_score,
            manual_average_score=overview.manual_average_score,
            accepted_average_score=overview.accepted_average_score,
            rejected_average_score=overview.rejected_average_score,
            first_forwarded_at=overview.first_forwarded_at,
            last_forwarded_at=overview.last_forwarded_at,
        )

    def _map_forwarded_bucket(self, bucket: Any) -> ForwardedBucketData:
        return ForwardedBucketData(
            bucket_start=bucket.bucket_start,
            bucket_end=bucket.bucket_end,
            total=bucket.total,
            manual_pending=bucket.manual_pending,
            auto_approved=bucket.auto_approved,
            auto_rejected=bucket.auto_rejected,
            average_score=bucket.average_score,
        )

    def _handle_http_error(self, exc: httpx.HTTPError, message: str) -> NoReturn:
        if isinstance(exc, httpx.TimeoutException):
            raise exceptions.TimeoutServiceError(message) from exc
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            if status_code == HTTPStatus.NOT_FOUND:
                raise exceptions.NotFoundError(message) from exc
            if status_code == HTTPStatus.CONFLICT:
                raise exceptions.OperationNotAllowedError(message) from exc
            if status_code in {HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY}:
                raise exceptions.ValidationError(message) from exc
            if status_code in {HTTPStatus.FORBIDDEN, HTTPStatus.UNAUTHORIZED}:
                raise exceptions.PermissionDeniedError(message) from exc
            raise exceptions.APIServiceError(message) from exc
        raise exceptions.DependencyUnavailableError(message) from exc
