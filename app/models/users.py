import datetime

from pydantic import BaseModel

from app.api.v1.users.requests import RegistryUserRequest, CompanyData, Contacts
from app.utils.types import TypesOfUser, LegalFormat


class UserCreateDTO(RegistryUserRequest):
    pass


class UserFillingDTO(BaseModel):
    city_id: int
    type: TypesOfUser
    main_category: list[int] | None = None


class CompanyDataDTO(BaseModel):
    type: LegalFormat
    company_name: str | None = None
    legal_address: str | None = None
    inn: str | None = None
    ogrn: str | None = None
    ogrnip: str | None = None
    kpp: str | None = None


class ContactDTO(Contacts):
    ...


class UpdateUserDTO(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None


class ContactsDTO(ContactDTO):
    id: int


class ReviewDTO(BaseModel):
    user: "UserShortDTO"
    stars: float
    text: str | None = None
    created_at: str


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
    legal_info: CompanyDataDTO | None = None
    rating: float | None = None
    updated_at: datetime.datetime


class UserShortDTO(BaseModel):
    id: int
    full_name: str
    city: str
    avatar: str | None = None



