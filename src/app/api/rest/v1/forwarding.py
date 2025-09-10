import uuid
from typing import Literal

from fastapi import APIRouter, Body, Depends, Path, Query

from app.utils.schemas import PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import ForwardingIn, ForwardingOut, ForwardingUpdate, UserSchema

router = APIRouter()


@router.post("/forwarding", response_model=ForwardingOut, status_code=201)
async def create_forwarding(data: ForwardingIn, current_user: UserSchema = Depends(get_current_user)) -> ForwardingOut:  # type: ignore[empty-body]
    pass


@router.get("/forwarding", response_model=PaginatedResponse[ForwardingOut], status_code=200)
async def search_forwarding(  # type: ignore[empty-body]
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    route_id: uuid.UUID | None = Query(default=None, alias="routeId"),
    is_valid: bool | None | Literal["not_set"] = Query(default="not_set", alias="isValid"),
    is_hidden: bool | None | Literal["not_set"] = Query(default=None, alias="isHidden"),
    document_id: uuid.UUID | None = Query(default=None, alias="documentId"),
    sender_id: uuid.UUID | None = Query(default=None, alias="senderId"),
    recipient_id: uuid.UUID | None = Query(default=None, alias="recipientId"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[ForwardingOut]:
    pass


@router.get("/forwarding/{forwardingId}", response_model=ForwardingOut, status_code=200)
async def get_forwarding(  # type: ignore[empty-body]
    forwarding_id: uuid.UUID = Path(alias="forwardingId"), current_user: UserSchema = Depends(get_current_user)
) -> ForwardingOut:
    pass


@router.delete("/forwarding/{forwardingId}", status_code=204)
async def delete_forwarding(
    forwarding_id: uuid.UUID = Path(alias="forwardingId"), current_user: UserSchema = Depends(get_current_user)
) -> None:
    pass


@router.patch("/forwarding/{forwardingId}", response_model=ForwardingOut, status_code=200)
async def edit_forwarding(  # type: ignore[empty-body]
    forwarding_id: uuid.UUID = Path(alias="forwardingId"),
    data: ForwardingUpdate = Body(),
    current_user: UserSchema = Depends(get_current_user),
) -> ForwardingOut:
    pass
