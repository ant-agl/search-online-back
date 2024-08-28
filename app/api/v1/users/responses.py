from pydantic import BaseModel

from app.api.v1.users.requests import Contacts
from app.models.common import ReviewsByStarsDTO
from app.models.users import ContactDTO, ContactsDTO, ReviewDTO, CompanyDataDTO
from app.utils.types import TypesOfUser


class UserContacts(BaseModel):
    result: list[ContactsDTO]


class UserInfo(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    types: list[str]


class CityInfo(BaseModel):
    id: int
    name: str


class UserAvatar(BaseModel):
    value: str | None = None


class UserResponse(BaseModel):
    id: int
    info: UserInfo
    city: CityInfo
    avatar: UserAvatar
    contacts: list[ContactsDTO]
    legal_info: CompanyDataDTO | None = None
    rating: float | None = None
    full_filled: bool
    is_blocked: bool
    updated_at: str


class Meta(BaseModel):
    page: int
    total_items: int
    total_pages: int
    items_per_page: int


class ReviewsResponse(BaseModel):
    by_stars: list[ReviewsByStarsDTO | None]
    result: list[ReviewDTO]
    meta: Meta

