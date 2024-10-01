from pydantic import BaseModel, EmailStr, field_validator, model_validator, Field

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
    is_hidden: bool = False


class CompanyData(BaseModel):
    type: LegalFormat
    company_name: str | None = None
    legal_address: str | None = None
    inn: str | None = None
    ogrn: str | None = None
    ogrnip: str | None = None
    kpp: str | None = None

    @model_validator(mode="after")
    def validate_company(self):
        err = ""
        if self.type.value == "ooo":
            ooo_required = [
                "company_name", "legal_address",
                "inn", "ogrn", "kpp",
            ]
            for val in ooo_required:
                if val not in self.model_fields_set:
                    err += f"Поле {val} должно быть заполнено для OOO\n"
        elif self.type.value == "individual":
            individual_required = [
                "company_name", "inn", "ogrnip",
            ]
            for val in individual_required:
                if val not in self.model_fields_set:
                    err += f"Поле {val} должно быть заполнено для ИП\n"
        elif self.type.value == "self":
            self_required = [
                "company_name", "inn",
            ]
            for val in self_required:
                if val not in self.model_fields_set:
                    err += f"Поле {val} должно быть заполнено для Самозанятых"
        elif self.type.value == "physical":
            return self

        if err != "":
            print(err)
            raise UnprocessableApiException(f"Не заполнены обязательные поля: \n {err}")

        return self


class FullRegistryUserRequest(BaseModel):
    city_id: int
    type: TypesOfUser
    contacts: list[Contacts]
    main_category: list[int] | None = None
    company_data: CompanyData | None = None

    # @model_validator(mode="before")
    # def validate_company(self):
    #     print(self)

    @model_validator(mode="after")
    def validate_field_type(self):
        if self.type == TypesOfUser.seller:
            if self.main_category is None or self.company_data is None:
                raise UnprocessableApiException(
                    "Не заполнены обязательные поля для продавца"
                )
        return self
    

class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    city_id: int | None = None


class UpdateContactRequest(BaseModel):
    new_value: str | None = None
    is_hidden: bool | None = None


class CreateSellerReviewRequest(BaseModel):
    stars: float = Field(default=0.5, le=5, gt=0.5)
    text: str | None = None


class ReportRequest(BaseModel):
    reason: str
