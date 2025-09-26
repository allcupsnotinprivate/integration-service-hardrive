from datetime import datetime
from uuid import UUID

from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from starlette import status
from starlette.responses import JSONResponse

from app.infrastructure.router_service.http.schemas import ProcessStatus
from app.service_layer import ADataStoreService
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import (
    DocumentCreatedResponse,
    DocumentForwardingRequest,
    DocumentHistoryItem,
    DocumentSummary,
    ForwardCreatedResponse,
    ManualDocumentRequest,
    UserSchema,
)

router = APIRouter()


@router.get(
    "/documents/search",
    response_model=PaginatedResponse[DocumentSummary],
    status_code=200,
    description=(
        "История отражает связи между документами и маршрутами. "
        "Для одного документа может существовать несколько маршрутов."
    ),
)
@inject
async def search_documents(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    name: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None, alias="createdFrom"),
    created_to: datetime | None = Query(default=None, alias="createdTo"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[DocumentSummary]:
    documents_search_result = await data_store.search_documents(
        page=page,
        per_page=per_page,
        name=name,
        created_from=created_from,
        created_to=created_to,
    )
    items = [
        DocumentSummary(id=doc.id, name=doc.name, created_at=doc.created_at) for doc in documents_search_result.items
    ]
    meta = PageMeta(
        page=documents_search_result.meta.page,
        per_page=documents_search_result.meta.per_page,
        total=documents_search_result.meta.total,
        total_pages=documents_search_result.meta.total_pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("/documents/manual", response_model=DocumentCreatedResponse, status_code=201)
@inject
async def admit_document(
    payload: ManualDocumentRequest,
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> DocumentCreatedResponse:
    if not payload.name.strip() or not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and content must not be empty")
    document_id = await data_store.create_manual_document(name=payload.name, content=payload.content)
    return DocumentCreatedResponse(id=document_id)


@router.post("/documents/{documentId}/forwardings", response_model=ForwardCreatedResponse, status_code=201)
@inject
async def forward_document(
    payload: DocumentForwardingRequest,
    document_id: UUID = Path(alias="documentId"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> ForwardCreatedResponse:
    forward_id = await data_store.forward_document(
        purpose=payload.purpose,
        sender_id=payload.sender_id,
        recipient_id=payload.recipient_id,
        document_id=document_id,
    )
    return ForwardCreatedResponse(id=forward_id)


@router.get("/documents/history", response_model=PaginatedResponse[DocumentHistoryItem], status_code=200)
@inject
async def document_history(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    document_id: UUID | None = Query(default=None, alias="documentId"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    status_filter: ProcessStatus | None = Query(default=None, alias="status"),
    started_from: datetime | None = Query(default=None, alias="startedFrom"),
    started_to: datetime | None = Query(default=None, alias="startedTo"),
    completed_from: datetime | None = Query(default=None, alias="completedFrom"),
    completed_to: datetime | None = Query(default=None, alias="completedTo"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[DocumentHistoryItem]:
    document_history_search_results = await data_store.get_document_history(
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
        DocumentHistoryItem(
            document_id=record.document_id,
            route_id=record.route_id,
            document_created_at=record.document_created_at,
            route_created_at=record.route_created_at,
            sender_id=record.sender_id,
            route_status=record.route_status,
            document_name=record.document_name,
            first_chunk_preview=record.first_chunk_preview,
            predicted_recipient_id=record.predicted_recipient_id,
            prediction_confidence=record.prediction_confidence,
            investigation_duration_seconds=record.investigation_duration_seconds,
        )
        for record in document_history_search_results.items
    ]

    meta = PageMeta(
        page=document_history_search_results.meta.page,
        per_page=document_history_search_results.meta.per_page,
        total=document_history_search_results.meta.total,
        total_pages=document_history_search_results.meta.total_pages,
    )

    return PaginatedResponse(items=items, meta=meta)


@router.get(
    "/documents/history/export",
    deprecated=True,
    include_in_schema=True,
)
async def export_history_placeholder() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "detail": "Export to XLS will be implemented once router service exposes bulk data APIs.",
        },
    )
