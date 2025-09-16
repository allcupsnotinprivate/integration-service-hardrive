from uuid import UUID

from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, Query

from app.infrastructure import ARouterServiceHTTPClient
from app.service_layer import ADataStoreService
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import ForwardCreatedResponse, ForwardDocumentRequest, ForwardingRecord, UserSchema

router = APIRouter()


@router.get("/forwardings", response_model=PaginatedResponse[ForwardingRecord], status_code=200)
@inject
async def list_forwardings(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, alias="perPage"),
    document_id: UUID | None = Query(default=None, alias="documentId"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    recipient_id: UUID | None = Query(default=None, alias="recipientId"),
    route_id: UUID | None = Query(default=None, alias="routeId"),
    is_valid: bool | None = Query(default=None, alias="isValid"),
    is_hidden: bool | None = Query(default=None, alias="isHidden"),
    purpose: str | None = Query(default=None),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[ForwardingRecord]:
    forwardings_search_result = await data_store.list_forwardings(
        page=page,
        per_page=per_page,
        document_id=document_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        route_id=route_id,
        is_valid=is_valid,
        is_hidden=is_hidden,
        purpose=purpose,
    )

    items = [
        ForwardingRecord(
            id=item.id,
            document_id=item.document_id,
            sender_id=item.sender_id,
            recipient_id=item.recipient_id,
            route_id=item.route_id,
            purpose=item.purpose,
            is_valid=item.is_valid,
            is_hidden=item.is_hidden,
            score=item.score,
            created_at=item.created_at,
        )
        for item in forwardings_search_result.items
    ]
    meta = PageMeta(
        page=forwardings_search_result.meta.page,
        per_page=forwardings_search_result.meta.per_page,
        total=forwardings_search_result.meta.total,
        total_pages=forwardings_search_result.meta.total_pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("/forwardings", response_model=ForwardCreatedResponse, status_code=201)
@inject
async def forward_document(
    payload: ForwardDocumentRequest,
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> ForwardCreatedResponse:
    forward_id = await data_store.forward_document(
        purpose=payload.purpose,
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        document_id=payload.document_id,
    )
    return ForwardCreatedResponse(id=forward_id)
