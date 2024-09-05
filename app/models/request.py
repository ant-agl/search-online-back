from pydantic import BaseModel

from app.models.users import UserShortDTO


class RequestCategory(BaseModel):
    id: int
    value: str


class RequestPhotos(BaseModel):
    id: int
    link: str
    index: int


class RequestDTO(BaseModel):
    id: int
    creator: UserShortDTO
    title: str
    max_price: int
    max_days: int | None = None
    photos: list[RequestPhotos | None]
    created_at: str


class RequestDTOExtended(BaseModel):
    description: str
    category: RequestCategory
    updated_at: str
    clicks: int


