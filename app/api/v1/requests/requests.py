from pydantic import BaseModel

from app.utils.types import ItemType


class NewRequest(BaseModel):
    type: ItemType
    category_id: int
    title: str
    description: str
    max_price: int | None = None
    max_production_time: int | None = None
