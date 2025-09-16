from datetime import datetime
from uuid import UUID

from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, Path, Query

from app.infrastructure.router_service.http.schemas import ProcessStatus
from app.service_layer import ADataStoreService
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
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, alias="perPage"),
    document_id: UUID | None = Query(default=None, alias="documentId"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    status_filter: ProcessStatus | None = Query(default=None, alias="status"),
    started_from: datetime | None = Query(default=None, alias="startedFrom"),
    started_to: datetime | None = Query(default=None, alias="startedTo"),
    completed_from: datetime | None = Query(default=None, alias="completedFrom"),
    completed_to: datetime | None = Query(default=None, alias="completedTo"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[RouteRecord]:
    routes_search_result = await data_store.list_routes(
        page=page,
        per_page=per_page,
        document_id=document_id,
        sender_id=sender_id,
        status_filter=status_filter,
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
        for item in routes_search_result.items
    ]
    meta = PageMeta(
        page=routes_search_result.meta.page,
        per_page=routes_search_result.meta.per_page,
        total=routes_search_result.meta.total,
        total_pages=routes_search_result.meta.total_pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.get("/routes/{routeId}", response_model=RouteDetails, status_code=200)
@inject
async def retrieve_route(
    route_id: UUID = Path(alias="routeId"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> RouteDetails:
    route = await data_store.retrieve_route(route_id=route_id)
    return RouteDetails(
        id=route.id,
        status=route.status,
        started_at=route.started_at,
        completed_at=route.completed_at,
    )


@router.post("/routes/{routeId}/investigate", status_code=202)
@inject
async def trigger_manual_investigation(
    route_id: UUID = Path(alias="routeId"),
    payload: RouteInvestigationRequest | None = None,
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> None:
    allow_recovery = payload.allow_recovery if payload else False
    await data_store.trigger_manual_investigation(route_id=route_id, allow_recovery=allow_recovery)


@router.get("/routes/{routeId}/results", response_model=RouteInvestigationRecord, status_code=200)
@inject
async def get_route_investigation(
    route_id: UUID = Path(alias="routeId"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> RouteInvestigationRecord:
    result = await data_store.get_route_investigation(route_id=route_id)
    forwards = [
        RouteForwardRecord(
            sender_id=forward.sender_id,
            recipient_id=forward.recipient_id,
            score=forward.score,
        )
        for forward in result.forwards
    ]
    return RouteInvestigationRecord(status=result.status, forwards=forwards)
