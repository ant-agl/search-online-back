from pydantic import BaseModel

from app.api.v1.users.requests import Contacts
from app.models.users import ContactDTO, ContactsDTO
from app.utils.types import TypesOfUser


class UserContacts(BaseModel):
    result: list[ContactsDTO]


class UserInfo(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    type: str


class CityInfo(BaseModel):
    id: int
    name: str


class UserAvatar(BaseModel):
    value: str


class UserResponse(BaseModel):
    id: int
    info: UserInfo
    city: CityInfo
    avatar: UserAvatar
    contacts: list[ContactsDTO]
    legal_info: None = None
    full_filled: bool
    is_blocked: bool
    updated_at: str


