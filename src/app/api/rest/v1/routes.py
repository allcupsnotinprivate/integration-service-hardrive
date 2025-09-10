import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query

from app.utils.schemas import PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import RouteOut, UserSchema

router = APIRouter()


@router.get("/routes", response_model=PaginatedResponse[RouteOut], status_code=200)
async def search_routes(  # type: ignore[empty-body]
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    document_id: uuid.UUID | None = Query(default=None, alias="documentId"),
    status: Literal["pending", "in_progress", "completed", "failed"] | None = Query(default=None),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[RouteOut]:
    pass


@router.get("/routes/{routeId}", response_model=RouteOut, status_code=200)
async def get_route(  # type: ignore[empty-body]
    route_id: uuid.UUID = Path(alias="routeId"), current_user: UserSchema = Depends(get_current_user)
) -> RouteOut:
    pass
