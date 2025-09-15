from aioinject import Injected
from aioinject.ext.fastapi import inject
from fastapi import APIRouter, Depends, Query

from app.infrastructure import ARouterServiceHTTPClient
from app.utils.schemas import PageMeta, PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import AgentCreatedResponse, AgentRecord, AgentRegisterRequest, UserSchema

router = APIRouter()


@router.get("/agents", response_model=PaginatedResponse[AgentRecord], status_code=200)
@inject
async def list_agents(
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, alias="perPage"),
    name: str | None = Query(default=None),
    description: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_default_recipient: bool | None = Query(default=None, alias="isDefaultRecipient"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[AgentRecord]:
    response = await router_client.search_agents(
        page=page,
        page_size=per_page,
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
        for agent in response.items
    ]
    meta = PageMeta(
        page=response.page_info.page,
        per_page=response.page_info.page_size,
        total=response.page_info.total,
        total_pages=response.page_info.pages,
    )
    return PaginatedResponse(items=items, meta=meta)


@router.post("/agents", response_model=AgentCreatedResponse, status_code=201)
@inject
async def register_agent(
    payload: AgentRegisterRequest,
    router_client: Injected[ARouterServiceHTTPClient] = Depends(),
    current_user: UserSchema = Depends(get_current_user),
) -> AgentCreatedResponse:
    response = await router_client.register_agent(
        name=payload.name.strip(),
        description=payload.description,
        is_default_recipient=payload.is_default_recipient,
    )
    return AgentCreatedResponse(id=response.id)
