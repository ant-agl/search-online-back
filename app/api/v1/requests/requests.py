from pydantic import BaseModel, Field, HttpUrl

from app.utils.types import ItemType


class NewRequest(BaseModel):
    type: ItemType
    category_id: int
    title: str
    description: str
    max_price: int | None = None
    currency: str = "RUB"
    max_production_time: int | None = None
    photos: list[HttpUrl] | None = Field(description="Список ссылок на фото")
