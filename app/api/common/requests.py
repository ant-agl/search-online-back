from pydantic import BaseModel

from app.utils.types import ItemType


class CreateCategory(BaseModel):
    name: str
    depend_on: int | None = None
    type: ItemType
