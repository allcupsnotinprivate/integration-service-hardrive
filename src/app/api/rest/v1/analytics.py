from dataclasses import asdict

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
    current_user: UserSchema = Depends(get_current_user),
) -> AnalyticsOverview:
    overview = await data_store.get_analytics_overview()
    return AnalyticsOverview.model_validate(asdict(overview))


@router.get("/analytics/routes/summary", response_model=AnalyticsRoutesSummary, status_code=200)
@inject
async def get_routes_summary(
    window: AnalyticsTimeWindow = Query(default=AnalyticsTimeWindow.HOUR),
    bucket_limit: int | None = Query(default=None, ge=1, le=336),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> AnalyticsRoutesSummary:
    summary = await data_store.get_routes_summary(window=window, bucket_limit=bucket_limit)
    return AnalyticsRoutesSummary.model_validate(asdict(summary))


@router.get("/analytics/routes/predictions", response_model=AnalyticsForwardedSummary, status_code=200)
@inject
async def get_forwarded_summary(
    window: AnalyticsTimeWindow = Query(default=AnalyticsTimeWindow.HOUR),
    bucket_limit: int | None = Query(default=None, ge=1, le=336),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> AnalyticsForwardedSummary:
    summary = await data_store.get_forwarded_summary(window=window, bucket_limit=bucket_limit)
    return AnalyticsForwardedSummary.model_validate(asdict(summary))
