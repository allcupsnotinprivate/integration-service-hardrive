from datetime import datetime
from uuid import UUID

import httpx
from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from starlette import status

from app.infrastructure import ARouterServiceHTTPClient
from app.infrastructure.router_service.http.schemas import ProcessStatus
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import (
    RouteDetails,
    RouteForwardRecord,
    RouteInvestigationRecord,
    RouteInvestigationRequest,
    RouteRecord,
    UserSchema,
)

router = APIRouter()


@router.get("/routes", response_model=PaginatedResponse[RouteRecord], status_code=200)
@inject
async def list_routes(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, alias="perPage"),
    document_id: UUID | None = Query(default=None, alias="documentId"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    status_filter: ProcessStatus | None = Query(default=None, alias="status"),
    started_from: datetime | None = Query(default=None, alias="startedFrom"),
    started_to: datetime | None = Query(default=None, alias="startedTo"),
    completed_from: datetime | None = Query(default=None, alias="completedFrom"),
    completed_to: datetime | None = Query(default=None, alias="completedTo"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[RouteRecord]:
    response = await router_client.search_routes(
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

    items = [
        RouteRecord(
            id=item.id,
            document_id=item.document_id,
            sender_id=item.sender_id,
            status=item.status,
            started_at=item.started_at,
            completed_at=item.completed_at,
            created_at=item.created_at,
        )
        for item in response.items
    ]
    meta = PageMeta(
        page=response.page_info.page,
        per_page=response.page_info.page_size,
        total=response.page_info.total,
        total_pages=response.page_info.pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.get("/routes/{routeId}", response_model=RouteDetails, status_code=200)
@inject
async def retrieve_route(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    route_id: UUID = Path(alias="routeId"),
    current_user: UserSchema = Depends(get_current_user),
) -> RouteDetails:
    try:
        route = await router_client.retrieve_route(route_id=route_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Route not found") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Router service unavailable") from exc

    return RouteDetails(
        id=route.id,
        status=route.status,
        started_at=route.started_at,
        completed_at=route.completed_at,
    )


@router.post("/routes/{routeId}/investigate", status_code=202)
@inject
async def trigger_manual_investigation(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    route_id: UUID = Path(alias="routeId"),
    payload: RouteInvestigationRequest | None = None,
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    allow_recovery = payload.allow_recovery if payload else False
    try:
        await router_client.investigate_routing(route_id=route_id, allow_recovery=allow_recovery)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Unable to trigger investigation") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Router service unavailable") from exc


@router.get("/routes/{routeId}/results", response_model=RouteInvestigationRecord, status_code=200)
@inject
async def get_route_investigation(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    route_id: UUID = Path(alias="routeId"),
    current_user: UserSchema = Depends(get_current_user),
) -> RouteInvestigationRecord:
    try:
        result = await router_client.retrieve_investigation_results(route_id=route_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Investigation not found") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Router service unavailable") from exc

    forwards = [
        RouteForwardRecord(
            sender_id=forward.sender_id,
            recipient_id=forward.recipient_id,
            score=forward.score,
        )
        for forward in result.forwards
    ]
    return RouteInvestigationRecord(status=result.status, forwards=forwards)
