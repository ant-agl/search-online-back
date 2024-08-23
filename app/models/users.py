import datetime

from pydantic import BaseModel

from app.api.v1.users.requests import RegistryUserRequest, CompanyData, Contacts
from app.utils.types import TypesOfUser


class UserCreateDTO(RegistryUserRequest):
    pass


class UserFillingDTO(BaseModel):
    city_id: int
    type: TypesOfUser
    main_category: int | None = None


class ComponyDataDTO(CompanyData):
    ...


class ContactDTO(Contacts):
    ...


class UpdateUserDTO(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None


class ContactsDTO(ContactDTO):
    id: int


class UserDTO(BaseModel):
    id: int
    first_name: str
    last_name: str
    middle_name: str | None = None
    types: list[str]
    city: str
    city_id: int
    avatar: str | None = None
    contacts: list[ContactsDTO]
    full_filled: bool
    is_blocked: bool
    legal_info: None
    updated_at: datetime.datetime


class UserShortDTO(BaseModel):
    id: int
    full_name: str
    city: str
    avatar: str | None = None
