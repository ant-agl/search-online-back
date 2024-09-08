from fastapi import Form
from pydantic import BaseModel, model_validator

from app.api.exceptions import UnprocessableApiException
from app.utils.types import ItemType


class PriceRange(BaseModel):
    min_price: float | None = None
    max_price: float | None = None
    fix_price: float | None = None
    currency: str = "RUB"

    @model_validator(mode="after")
    def validate_price(self):
        if self.fix_price is None:
            if self.min_price is None and self.max_price is None:
                raise UnprocessableApiException(
                    "Вам нужно указать диапазон цен или укажите фиксированную цену"
                )
            if self.min_price >= self.max_price:
                raise UnprocessableApiException(
                    "Минимальная цена должна быть ниже максимальной"
                )
        return self


class ProductionTime(BaseModel):
    from_time: int | None = None
    to_time: int | None = None


class Location(BaseModel):
    city_id: int
    address: str | None = None


class CreateItem(BaseModel):
    type: ItemType
    title: str
    description: str
    category_id: int
    price: PriceRange
    is_delivered: bool = Form(False)
    production_time: ProductionTime | None = None
    location: Location
    comment: str | None = None


class UpdateItemMainInfo(BaseModel):
    title: str | None = None
    description: str | None = None
    is_delivered: bool = False
    comment: str | None = None


class UpdateItemLocation(BaseModel):
    city_id: int | None = None
    address: str | None = None


class UpdateItem(BaseModel):
    info: UpdateItemMainInfo | None = None
    price: PriceRange | None = None
    production_time: ProductionTime | None = None
    location: UpdateItemLocation
    category_id: int | None = None


class GetCards(BaseModel):
    type: ItemType
    category_id: int | None = None
    city_id: int | None = None
    from_price: float | None = None
    to_price: float | None = None
    from_days: int | None = None
    to_days: int | None = None
    q: str | None = None


class PostItemReview(BaseModel):
    stars: float
    text: str | None = None
