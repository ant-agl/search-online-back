from typing import Any

from pydantic import BaseModel

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
    offers: Any | None = None
    meta: dict | None = None
