from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class BaseAPISchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class PageMeta(BaseAPISchema):
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=1000)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)


class PaginatedResponse[T](BaseAPISchema):
    items: list[T]
    meta: PageMeta
