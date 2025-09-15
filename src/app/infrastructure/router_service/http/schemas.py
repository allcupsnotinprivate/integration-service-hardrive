from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ProcessStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class PageMeta(BaseSchema):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(alias="pageSize", ge=1)
    pages: int = Field(ge=0)


class DocumentOut(BaseSchema):
    id: UUID = Field()


class DocumentRead(BaseSchema):
    id: UUID = Field()
    name: str | None = Field(default=None)
    created_at: datetime = Field()


class DocumentSearchResponse(BaseSchema):
    items: list[DocumentRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class DocumentChunkRead(BaseSchema):
    id: UUID = Field()
    document_id: UUID = Field(alias="documentId")
    parent_id: UUID | None = Field(default=None, alias="parentId")
    content: str = Field()
    created_at: datetime = Field()


class DocumentChunkSearchResponse(BaseSchema):
    items: list[DocumentChunkRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class AgentOut(BaseSchema):
    id: UUID = Field()


class AgentRead(BaseSchema):
    id: UUID = Field()
    name: str = Field()
    description: str | None = Field(default=None)
    is_active: bool = Field()
    is_default_recipient: bool = Field()
    created_at: datetime = Field()


class AgentSearchResponse(BaseSchema):
    items: list[AgentRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class DocumentForwardedOut(BaseSchema):
    id: UUID = Field()


class ForwardedRead(BaseSchema):
    id: UUID = Field()
    document_id: UUID = Field(alias="documentId")
    sender_id: UUID | None = Field(default=None, alias="senderId")
    recipient_id: UUID = Field(alias="recipientId")
    route_id: UUID | None = Field(default=None, alias="routeId")
    purpose: str | None = Field(default=None)
    is_valid: bool | None = Field(default=None, alias="isValid")
    is_hidden: bool = Field(alias="isHidden")
    score: float | None = Field(default=None)
    created_at: datetime = Field()


class ForwardedSearchResponse(BaseSchema):
    items: list[ForwardedRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class DocumentForward(BaseSchema):
    sender_id: UUID = Field()
    recipient_ids: list[UUID] = Field()


class DocumentForwardsOut(BaseSchema):
    forwards: list[DocumentForward] = Field(default_factory=list)


class RouteRead(BaseSchema):
    id: UUID = Field()
    document_id: UUID = Field(alias="documentId")
    sender_id: UUID | None = Field(default=None, alias="senderId")
    status: ProcessStatus = Field()
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")


class RouteSearchResponse(BaseSchema):
    items: list[RouteRead] = Field(default_factory=list)
    page_info: PageMeta = Field(alias="pageInfo")


class RouteDocumentOut(BaseSchema):
    id: UUID = Field()
    status: ProcessStatus = Field()
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


class RouteForwardedOut(BaseSchema):
    sender_id: UUID | None = Field(default=None)
    recipient_id: UUID | None = Field(default=None)
    score: float | None = Field(default=None)


class RouteInvestigationOut(BaseSchema):
    status: ProcessStatus = Field()
    forwards: list[RouteForwardedOut] = Field(default_factory=list)