from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, Query

from app.service_layer import ADataStoreService
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import AgentCreatedResponse, AgentRecord, AgentRegisterRequest, UserSchema

router = APIRouter()


@router.get("/agents", response_model=PaginatedResponse[AgentRecord], status_code=200)
@inject
async def list_agents(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, alias="perPage"),
    name: str | None = Query(default=None),
    description: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_default_recipient: bool | None = Query(default=None, alias="isDefaultRecipient"),
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[AgentRecord]:
    agents_search_result = await data_store.list_agents(
        page=page,
        per_page=per_page,
        name=name,
        description=description,
        is_active=is_active,
        is_default_recipient=is_default_recipient,
    )

    items = [
        AgentRecord(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            is_active=agent.is_active,
            is_default_recipient=agent.is_default_recipient,
            created_at=agent.created_at,
        )
        for agent in agents_search_result.items
    ]
    meta = PageMeta(
        page=agents_search_result.meta.page,
        per_page=agents_search_result.meta.per_page,
        total=agents_search_result.meta.total,
        total_pages=agents_search_result.meta.total_pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("/agents", response_model=AgentCreatedResponse, status_code=201)
@inject
async def register_agent(
    payload: AgentRegisterRequest,
    data_store: Injected[ADataStoreService] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> AgentCreatedResponse:
    agent_id = await data_store.register_agent(
        name=payload.name,
        description=payload.description,
        is_default_recipient=payload.is_default_recipient,
    )
    return AgentCreatedResponse(id=agent_id)
