from pydantic import BaseModel, EmailStr

from app.utils.types import ItemType


class CreateCategory(BaseModel):
    name: str
    depend_on: int | None = None
    type: ItemType


class TechnicalRequest(BaseModel):
    contact_email: EmailStr
    text: str

