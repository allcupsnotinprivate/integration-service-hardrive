import uuid

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile

from app.utils.schemas import PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import DocumentOut, ManualDocumentIn, UploadDocumentForm, UserSchema

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentOut, status_code=201)
async def upload_document(  # type: ignore[empty-body]
    file: UploadFile = File(...),
    data: UploadDocumentForm = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> DocumentOut:
    pass


@router.post("/documents/new", response_model=DocumentOut, status_code=201)
async def new_manual_document(  # type: ignore[empty-body]
    data: ManualDocumentIn, current_user: UserSchema = Depends(get_current_user)
) -> DocumentOut:
    pass


@router.get("/documents", response_model=PaginatedResponse[DocumentOut], status_code=200)
async def search_documents(  # type: ignore[empty-body]
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[DocumentOut]:
    pass


@router.get("/documents/{documentId}", response_model=DocumentOut, status_code=200)
async def get_document(  # type: ignore[empty-body]
    document_id: uuid.UUID = Path(alias="documentId"), current_user: UserSchema = Depends(get_current_user)
) -> DocumentOut:
    pass


@router.delete("/documents/{documentId}", status_code=204)
async def delete_document(
    document_id: uuid.UUID = Path(alias="documentId"), current_user: UserSchema = Depends(get_current_user)
) -> None:
    pass
