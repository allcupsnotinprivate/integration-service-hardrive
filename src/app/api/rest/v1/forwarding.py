from uuid import UUID

from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.service_layer import ADataStoreService
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import (
    ForwardCreatedResponse,
    ForwardDocumentRequest,
    ForwardingRecord,
    ForwardingUpdateRequest,
    UserSchema,
)

router = APIRouter()


@router.get(
    "/forwardings",
    response_model=PaginatedResponse[ForwardingRecord],
    status_code=200,
    description=(
        "Если пересылка (`Forwarding`) связана с маршрутом (`routeId`), она считается предсказанной системой. "
        "Запись, привязанная только к документу, - добавлена вручную. Поле `isValid` пустое — требуется ручная "
        "валидация; `True` означает, что флаг установлен вручную или что `score` превысил системный порог. "
        "Флаг `isHidden=True` исключает запись из дальнейших предсказаний."
    ),
)
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


@router.post(
    "/forwardings",
    response_model=ForwardCreatedResponse,
    status_code=201,
    description=(
        "Создаёт ручную запись пересылки, связанную только с документом. Такие записи не "
        "привязаны к маршрутам и считаются добавленными вручную; для модерации используются флаги `isValid` и `isHidden`."
    ),
)
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


@router.patch("/forwardings/{forwardId}", response_model=ForwardingRecord, status_code=200)
@inject
async def update_forwarding(
    payload: ForwardingUpdateRequest,
    forward_id: UUID = Path(alias="forwardId"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> ForwardingRecord:
    if payload.purpose is None and payload.is_valid is None and payload.is_hidden is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    record = await data_store.update_forwarding(
        forward_id=forward_id,
        purpose=payload.purpose,
        is_valid=payload.is_valid,
        is_hidden=payload.is_hidden,
    )

    return ForwardingRecord(
        id=record.id,
        document_id=record.document_id,
        sender_id=record.sender_id,
        recipient_id=record.recipient_id,
        route_id=record.route_id,
        purpose=record.purpose,
        is_valid=record.is_valid,
        is_hidden=record.is_hidden,
        score=record.score,
        created_at=record.created_at,
    )
