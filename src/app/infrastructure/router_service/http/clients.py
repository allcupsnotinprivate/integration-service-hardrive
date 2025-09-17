import abc
import logging
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Self
from uuid import UUID

import httpx
from loguru import logger
from tenacity import AsyncRetrying, RetryCallState, before_sleep_log, retry_if_exception, stop_after_attempt

from .schemas import (
    AgentOut,
    AgentSearchResponse,
    DocumentChunkSearchResponse,
    DocumentForwardedOut,
    DocumentForwardsOut,
    DocumentOut,
    DocumentSearchResponse,
    ForwardedSearchResponse,
    ProcessStatus,
    RouteDocumentOut,
    RouteInvestigationOut,
    RouteSearchResponse,
)

RETRYABLE_STATUS_CODES = frozenset({408, 425, 429, 502, 503})


class ARouterServiceHTTPClient(abc.ABC):
    @abc.abstractmethod
    async def register_agent(
        self,
        *,
        name: str,
        description: str | None = None,
        is_default_recipient: bool = False,
    ) -> AgentOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_agents(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        is_default_recipient: bool | None = None,
    ) -> AgentSearchResponse:
        raise NotImplementedError

    @abc.abstractmethod
    async def admit_document(self, *, name: str, content: str) -> DocumentOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> DocumentSearchResponse:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_document_chunks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_id: UUID | None = None,
        parent_id: UUID | None = None,
        content: str | None = None,
    ) -> DocumentChunkSearchResponse:
        raise NotImplementedError

    @abc.abstractmethod
    async def forward_document(
        self,
        *,
        purpose: str | None,
        sender_id: UUID,
        recipient_id: UUID,
        document_id: UUID,
    ) -> DocumentForwardedOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def retrieve_document_forwards(self, *, document_id: UUID) -> DocumentForwardsOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_forwarded(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_id: UUID | None = None,
        sender_id: UUID | None = None,
        recipient_id: UUID | None = None,
        route_id: UUID | None = None,
        is_valid: bool | None = None,
        is_hidden: bool | None = None,
        purpose: str | None = None,
    ) -> ForwardedSearchResponse:
        raise NotImplementedError

    @abc.abstractmethod
    async def search_routes(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_id: UUID | None = None,
        sender_id: UUID | None = None,
        status: ProcessStatus | None = None,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        completed_from: datetime | None = None,
        completed_to: datetime | None = None,
    ) -> RouteSearchResponse:
        raise NotImplementedError

    @abc.abstractmethod
    async def initialize_routing(
        self,
        *,
        document_id: UUID,
        sender_id: UUID | None = None,
    ) -> RouteDocumentOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def retrieve_route(self, *, route_id: UUID) -> RouteDocumentOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def investigate_routing(self, *, route_id: UUID, allow_recovery: bool = False) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def retrieve_investigation_results(self, *, route_id: UUID) -> RouteInvestigationOut:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class RouterServiceHTTPClient(ARouterServiceHTTPClient):
    def __init__(
        self,
        base_url: str,
        *,
        retry_attempts: int = 3,
        retry_backoff_initial: float = 0.5,
        retry_backoff_max: float = 10.0,
        retry_backoff_multiplier: float = 2.0,
        retry_jitter: float = 0.1,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        self._base_url = f"{base_url.rstrip('/')}/api/v1"
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)
        self._retry_attempts = max(1, int(retry_attempts))
        self._retry_backoff_initial = max(0.0, float(retry_backoff_initial))
        self._retry_backoff_max = max(self._retry_backoff_initial, float(retry_backoff_max))
        self._retry_backoff_multiplier = max(1.0, float(retry_backoff_multiplier))
        self._retry_jitter = max(0.0, float(retry_jitter))

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def register_agent(
        self,
        *,
        name: str,
        description: str | None = None,
        is_default_recipient: bool = False,
    ) -> AgentOut:
        response = await self._request(
            "POST",
            "/intakes/agents/register",
            json=self._prepare_payload(
                {
                    "name": name,
                    "description": description,
                    "isDefaultRecipient": is_default_recipient,
                }
            ),
        )
        return AgentOut.model_validate(response.json())

    async def search_agents(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        is_default_recipient: bool | None = None,
    ) -> AgentSearchResponse:
        response = await self._request(
            "GET",
            "/intakes/agents/search",
            params=self._prepare_payload(
                {
                    "page": page,
                    "pageSize": page_size,
                    "name": name,
                    "description": description,
                    "isActive": is_active,
                    "isDefaultRecipient": is_default_recipient,
                }
            ),
        )
        return AgentSearchResponse.model_validate(response.json())

    async def admit_document(self, *, name: str, content: str) -> DocumentOut:
        response = await self._request(
            "POST",
            "/intakes/documents/admit",
            json=self._prepare_payload({"name": name, "content": content}),
        )
        return DocumentOut.model_validate(response.json())

    async def search_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> DocumentSearchResponse:
        response = await self._request(
            "GET",
            "/intakes/documents/search",
            params=self._prepare_payload(
                {
                    "page": page,
                    "pageSize": page_size,
                    "name": name,
                    "createdFrom": created_from,
                    "createdTo": created_to,
                }
            ),
        )
        return DocumentSearchResponse.model_validate(response.json())

    async def search_document_chunks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_id: UUID | None = None,
        parent_id: UUID | None = None,
        content: str | None = None,
    ) -> DocumentChunkSearchResponse:
        response = await self._request(
            "GET",
            "/intakes/documents/chunks/search",
            params=self._prepare_payload(
                {
                    "page": page,
                    "pageSize": page_size,
                    "documentId": document_id,
                    "parentId": parent_id,
                    "content": content,
                }
            ),
        )
        return DocumentChunkSearchResponse.model_validate(response.json())

    async def forward_document(
        self,
        *,
        purpose: str | None,
        sender_id: UUID,
        recipient_id: UUID,
        document_id: UUID,
    ) -> DocumentForwardedOut:
        response = await self._request(
            "POST",
            "/intakes/documents/forward",
            json=self._prepare_payload(
                {
                    "purpose": purpose,
                    "senderId": sender_id,
                    "recipientId": recipient_id,
                    "documentId": document_id,
                }
            ),
        )
        return DocumentForwardedOut.model_validate(response.json())

    async def retrieve_document_forwards(self, *, document_id: UUID) -> DocumentForwardsOut:
        response = await self._request(
            "GET",
            "/intakes/documents/forwards/retrieve",
            params=self._prepare_payload({"documentId": document_id}),
        )
        return DocumentForwardsOut.model_validate(response.json())

    async def search_forwarded(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_id: UUID | None = None,
        sender_id: UUID | None = None,
        recipient_id: UUID | None = None,
        route_id: UUID | None = None,
        is_valid: bool | None = None,
        is_hidden: bool | None = None,
        purpose: str | None = None,
    ) -> ForwardedSearchResponse:
        response = await self._request(
            "GET",
            "/intakes/forwards/search",
            params=self._prepare_payload(
                {
                    "page": page,
                    "pageSize": page_size,
                    "documentId": document_id,
                    "senderId": sender_id,
                    "recipientId": recipient_id,
                    "routeId": route_id,
                    "isValid": is_valid,
                    "isHidden": is_hidden,
                    "purpose": purpose,
                }
            ),
        )
        return ForwardedSearchResponse.model_validate(response.json())

    async def search_routes(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_id: UUID | None = None,
        sender_id: UUID | None = None,
        status: ProcessStatus | None = None,
        started_from: datetime | None = None,
        started_to: datetime | None = None,
        completed_from: datetime | None = None,
        completed_to: datetime | None = None,
    ) -> RouteSearchResponse:
        response = await self._request(
            "GET",
            "/intakes/routes/search",
            params=self._prepare_payload(
                {
                    "page": page,
                    "pageSize": page_size,
                    "documentId": document_id,
                    "senderId": sender_id,
                    "status": status,
                    "startedFrom": started_from,
                    "startedTo": started_to,
                    "completedFrom": completed_from,
                    "completedTo": completed_to,
                }
            ),
        )
        return RouteSearchResponse.model_validate(response.json())

    async def initialize_routing(
        self,
        *,
        document_id: UUID,
        sender_id: UUID | None = None,
    ) -> RouteDocumentOut:
        response = await self._request(
            "POST",
            "/routes/initialize",
            json=self._prepare_payload({"document_id": document_id, "sender_id": sender_id}),
        )
        return RouteDocumentOut.model_validate(response.json())

    async def retrieve_route(self, *, route_id: UUID) -> RouteDocumentOut:
        response = await self._request(
            "GET",
            "/routes/retrieve",
            params={"id": str(route_id)},
        )
        return RouteDocumentOut.model_validate(response.json())

    async def investigate_routing(self, *, route_id: UUID, allow_recovery: bool = False) -> None:
        await self._request(
            "POST",
            "/routes/investigate",
            params={"routeId": str(route_id)},
            json=self._prepare_payload({"allow_recovery": allow_recovery}),
        )

    async def retrieve_investigation_results(self, *, route_id: UUID) -> RouteInvestigationOut:
        response = await self._request(
            "GET",
            "/routes/investigations/forwards/fetch",
            params={"routeId": str(route_id)},
        )
        return RouteInvestigationOut.model_validate(response.json())

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        async for attempt in self._retrying():
            with attempt:
                response = await self._client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                )
                response.raise_for_status()
                return response
        raise RuntimeError("RouterServiceHTTPClient retry loop exited unexpectedly")

    def _prepare_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        return {key: self._serialize_value(value) for key, value in data.items() if value is not None}

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, ProcessStatus):
            return value.value
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._serialize_value(item) for key, item in value.items() if item is not None}
        return value

    def _retrying(self) -> AsyncRetrying:
        return AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self._retry_attempts),
            retry=retry_if_exception(self._is_retryable_exception),
            wait=self._compute_retry_wait,
            before_sleep=before_sleep_log(logger, logging.WARNING),  # type: ignore[arg-type]
        )

    @staticmethod
    def _is_retryable_exception(exception: BaseException) -> bool:
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            return status_code >= 500 or status_code in RETRYABLE_STATUS_CODES
        if isinstance(exception, httpx.RequestError):
            return True
        return False

    def _compute_retry_wait(self, retry_state: RetryCallState) -> float:
        attempt = max(1, retry_state.attempt_number)
        base_wait = self._retry_backoff_initial * (self._retry_backoff_multiplier ** (attempt - 1))
        base_wait = min(base_wait, self._retry_backoff_max)
        if self._retry_jitter:
            jitter_upper_bound = base_wait * self._retry_jitter
            base_wait = min(base_wait + random.uniform(0.0, jitter_upper_bound), self._retry_backoff_max)  # nosec B311: not used for security
        exception = retry_state.outcome.exception() if retry_state.outcome else None
        retry_after = self._extract_retry_after(exception)
        if retry_after is not None:
            base_wait = max(base_wait, retry_after)
        return base_wait

    @staticmethod
    def _extract_retry_after(exception: BaseException | None) -> float | None:
        if not isinstance(exception, httpx.HTTPStatusError):
            return None
        header_value = exception.response.headers.get("Retry-After")
        if header_value is None:
            return None
        return RouterServiceHTTPClient._parse_retry_after(header_value)

    @staticmethod
    def _parse_retry_after(value: str) -> float | None:
        stripped = value.strip()
        if not stripped:
            return None
        try:
            seconds = float(stripped)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(stripped)
            except (TypeError, ValueError):
                return None
            if retry_at is None:
                return None
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, seconds)
