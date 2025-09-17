import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Generic, NoReturn, TypeVar
from uuid import UUID

import httpx

from app import exceptions
from app.infrastructure import ARouterServiceHTTPClient
from app.infrastructure.router_service.http.schemas import ProcessStatus

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
    async def trigger_manual_investigation(self, *, route_id: UUID, allow_recovery: bool) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_route_investigation(self, *, route_id: UUID) -> RouteInvestigationData:
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
                    manual_review_available=route.status != ProcessStatus.COMPLETED,
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
