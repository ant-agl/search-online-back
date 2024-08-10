from pydantic import BaseModel, EmailStr, field_validator, model_validator

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
    hidden: bool = False


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

    @model_validator(mode="after")
    def validate_field_type(self):
        if self.type == TypesOfUser.seller:
            if self.main_category is None or self.company_data is None:
                raise UnprocessableApiException(
                    "Не заполнены обязательные поля для продавца"
                )
        return self
    



