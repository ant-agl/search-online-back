from pydantic import BaseModel, EmailStr, field_validator

from app.api.exceptions import UnprocessableApiException
from app.utils.types import TypesOfUser, ContactType, LegalFormat


class RegistryUserRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str


class Contacts(BaseModel):
    type: ContactType
    value: str
    hidden: bool


class CompanyData(BaseModel):
    legal_format: LegalFormat | None = None
    company_name: str
    address: str | None = None
    description: str


class FullRegistryUserRequest(BaseModel):
    city_id: int
    type: TypesOfUser
    contacts: list[Contacts]
    main_category: int | None = None
    company_data: CompanyData | None = None

    @field_validator("type")
    @classmethod
    def validate_field_type(cls, v):
        if v == TypesOfUser.seller.value:
            if cls.main_category is None or cls.company_data is None:
                raise UnprocessableApiException(
                    "Не заполнены обязательные поля для продавца"
                )



