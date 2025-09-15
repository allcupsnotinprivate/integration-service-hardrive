import abc
from datetime import datetime
from typing import Any, Self
from uuid import UUID

import httpx

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
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

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
                    "is_default_recipient": is_default_recipient,
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
                    "is_active": is_active,
                    "is_default_recipient": is_default_recipient,
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
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "document_id": document_id,
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
        response = await self._client.request(
            method,
            url,
            params=params,
            json=json,
        )
        response.raise_for_status()
        return response

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
