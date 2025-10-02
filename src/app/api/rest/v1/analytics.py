from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, Query

from app.infrastructure.router_service.http.schemas import AnalyticsTimeWindow
from app.service_layer import ADataStoreService

from ._dependencies import get_current_user
from ._schemas import (
    AnalyticsForwardedSummary,
    AnalyticsOverview,
    AnalyticsRoutesSummary,
    UserSchema,
)

router = APIRouter()


@router.get("/analytics/overview", response_model=AnalyticsOverview, status_code=200)
@inject
async def get_analytics_overview(
    data_store: Injected[ADataStoreService] = Depends(),
    time_from: datetime | None = Query(default=None, alias="timeFrom"),
    time_to: datetime | None = Query(default=None, alias="timeTo"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    recipient_id: UUID | None = Query(default=None, alias="recipientId"),
    current_user: UserSchema = Depends(get_current_user),
) -> AnalyticsOverview:
    overview = await data_store.get_analytics_overview(
        time_to=time_to, time_from=time_from, sender_id=sender_id, recipient_id=recipient_id
    )
    return AnalyticsOverview.model_validate(asdict(overview))


@router.get("/analytics/routes/summary", response_model=AnalyticsRoutesSummary, status_code=200)
@inject
async def get_routes_summary(
    window: AnalyticsTimeWindow = Query(default=AnalyticsTimeWindow.HOUR),
    bucket_limit: int | None = Query(default=None, ge=1, le=336),
    time_from: datetime | None = Query(default=None, alias="timeFrom"),
    time_to: datetime | None = Query(default=None, alias="timeTo"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    recipient_id: UUID | None = Query(default=None, alias="recipientId"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> AnalyticsRoutesSummary:
    summary = await data_store.get_routes_summary(
        window=window,
        bucket_limit=bucket_limit,
        time_to=time_to,
        time_from=time_from,
        sender_id=sender_id,
        recipient_id=recipient_id,
    )
    return AnalyticsRoutesSummary.model_validate(asdict(summary))


@router.get("/analytics/routes/predictions", response_model=AnalyticsForwardedSummary, status_code=200)
@inject
async def get_forwarded_summary(
    window: AnalyticsTimeWindow = Query(default=AnalyticsTimeWindow.HOUR),
    bucket_limit: int | None = Query(default=None, ge=1, le=336),
    time_from: datetime | None = Query(default=None, alias="timeFrom"),
    time_to: datetime | None = Query(default=None, alias="timeTo"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    recipient_id: UUID | None = Query(default=None, alias="recipientId"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> AnalyticsForwardedSummary:
    summary = await data_store.get_forwarded_summary(
        window=window,
        bucket_limit=bucket_limit,
        time_to=time_to,
        time_from=time_from,
        sender_id=sender_id,
        recipient_id=recipient_id,
    )
    return AnalyticsForwardedSummary.model_validate(asdict(summary))
