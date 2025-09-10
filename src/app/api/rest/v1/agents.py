import uuid

from fastapi import APIRouter, Body, Depends, Path, Query

from app.utils.schemas import PaginatedResponse

from ._dependencies import get_current_user
from ._schemas import AgentIn, AgentOut, AgentUpdate, UserSchema

router = APIRouter()


@router.post("/agents", response_model=AgentOut, status_code=201)
async def create_agent(data: AgentIn, current_user: UserSchema = Depends(get_current_user)) -> AgentOut:  # type: ignore[empty-body]
    pass


@router.get("/agents", response_model=PaginatedResponse[AgentOut], status_code=200)
async def search_agents(  # type: ignore[empty-body]
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, alias="perPage"),
    current_user: UserSchema = Depends(get_current_user),
) -> PaginatedResponse[AgentOut]:
    pass


@router.get("/agents/{agentId}", response_model=AgentOut, status_code=200)
async def get_agent(  # type: ignore[empty-body]
    agent_id: uuid.UUID = Path(alias="agentId"), current_user: UserSchema = Depends(get_current_user)
) -> AgentOut:
    pass


@router.delete("/agents/{agentId}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID = Path(alias="agentId"), current_user: UserSchema = Depends(get_current_user)
) -> None:
    pass


@router.patch("/agents/{agentId}", response_model=AgentOut, status_code=200)
async def edit_agent(  # type: ignore[empty-body]
    agent_id: uuid.UUID = Path(alias="agentId"),
    data: AgentUpdate = Body(),
    current_user: UserSchema = Depends(get_current_user),
) -> AgentOut:
    pass
