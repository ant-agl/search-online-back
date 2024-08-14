from pydantic import BaseModel

from app.models.common import CitiesDTO


class GetCities(BaseModel):
    result: list[CitiesDTO]


class Category(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    on_moderating: bool = False
    disabled: bool = False
    children: list["Category"] | None = None


class GetCategoryTree(BaseModel):
    result: list[Category]
