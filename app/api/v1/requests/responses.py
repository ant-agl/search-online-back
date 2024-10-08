from typing import Any

from pydantic import BaseModel, Field

from app.models.request import RequestDTO
from app.models.users import UserShortDTO


class Meta(BaseModel):
    page: int
    total_items: int
    total_pages: int
    items_per_page: int


class RequestsResponse(BaseModel):
    requests: list[RequestDTO]
    meta: Meta
    warning: str | None = None


class RequestResponse(BaseModel):
    request: RequestDTO
    offers: Any | None = Field(deprecated=True)
    meta: dict | None = Field(deprecated=True)
