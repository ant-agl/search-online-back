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


