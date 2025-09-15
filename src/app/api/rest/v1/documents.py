from datetime import datetime, timezone
from uuid import UUID

import httpx
from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from starlette.responses import JSONResponse

from app.infrastructure import ARouterServiceHTTPClient
from app.infrastructure.router_service.http.schemas import ProcessStatus
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import DocumentCreatedResponse, DocumentHistoryItem, DocumentSummary, ManualDocumentRequest, UserSchema

router = APIRouter()


@router.get("/documents", response_model=PaginatedResponse[DocumentSummary], status_code=200)
@inject
async def search_documents(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    name: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None, alias="createdFrom"),
    created_to: datetime | None = Query(default=None, alias="createdTo"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[DocumentSummary]:
    response = await router_client.search_documents(
        page=page,
        page_size=per_page,
        name=name,
        created_from=created_from,
        created_to=created_to,
    )
    items = [DocumentSummary(id=doc.id, name=doc.name, created_at=doc.created_at) for doc in response.items]
    meta = PageMeta(
        page=response.page_info.page,
        per_page=response.page_info.page_size,
        total=response.page_info.total,
        total_pages=response.page_info.pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("/documents/manual", response_model=DocumentCreatedResponse, status_code=201)
@inject
async def admit_document(
    payload: ManualDocumentRequest,
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> DocumentCreatedResponse:
    if not payload.name.strip() or not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and content must not be empty")
    response = await router_client.admit_document(name=payload.name.strip(), content=payload.content)
    return DocumentCreatedResponse(id=response.id)


@router.get("/documents/history", response_model=PaginatedResponse[DocumentHistoryItem], status_code=200)
@inject
async def document_history(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    document_id: UUID | None = Query(default=None, alias="documentId"),
    sender_id: UUID | None = Query(default=None, alias="senderId"),
    status_filter: ProcessStatus | None = Query(default=None, alias="status"),
    started_from: datetime | None = Query(default=None, alias="startedFrom"),
    started_to: datetime | None = Query(default=None, alias="startedTo"),
    completed_from: datetime | None = Query(default=None, alias="completedFrom"),
    completed_to: datetime | None = Query(default=None, alias="completedTo"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[DocumentHistoryItem]:
    routes_response = await router_client.search_routes(
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

    items: list[DocumentHistoryItem] = []
    for route in routes_response.items:
        first_chunk_preview: str | None = None
        try:
            chunks_response = await router_client.search_document_chunks(
                page=1,
                page_size=1,
                document_id=route.document_id,
            )
            if chunks_response.items:
                first_chunk_preview = chunks_response.items[0].content
        except httpx.HTTPError:
            first_chunk_preview = None

        investigation_status: ProcessStatus | None = None
        predicted_sender_id: UUID | None = None
        predicted_recipient_id: UUID | None = None
        prediction_confidence: float | None = None
        try:
            investigation = await router_client.retrieve_investigation_results(route_id=route.id)
            investigation_status = investigation.status
            if investigation.forwards:
                last_forward = investigation.forwards[-1]
                predicted_sender_id = last_forward.sender_id
                predicted_recipient_id = last_forward.recipient_id
                prediction_confidence = last_forward.score
        except httpx.HTTPError:
            investigation_status = None

        duration = None
        if route.started_at:
            end_time = route.completed_at or datetime.now(timezone.utc)
            duration = max((end_time - route.started_at).total_seconds(), 0.0)

        # Router service does not expose document metadata by id yet, so we cannot fetch the original name.
        document_name: str | None = None
        document_created_at = route.created_at

        items.append(
            DocumentHistoryItem(
                document_id=route.document_id,
                route_id=route.id,
                document_created_at=document_created_at,
                route_created_at=route.created_at,
                sender_id=route.sender_id,
                route_status=route.status,
                investigation_status=investigation_status,
                document_name=document_name,
                first_chunk_preview=first_chunk_preview,
                predicted_sender_id=predicted_sender_id,
                predicted_recipient_id=predicted_recipient_id,
                prediction_confidence=prediction_confidence,
                investigation_duration_seconds=duration,
                manual_review_available=route.status != ProcessStatus.COMPLETED,
                manual_review_endpoint=f"/api/v1/routes/{route.id}/investigate",
            )
        )

    meta = PageMeta(
        page=routes_response.page_info.page,
        per_page=routes_response.page_info.page_size,
        total=routes_response.page_info.total,
        total_pages=routes_response.page_info.pages,
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
