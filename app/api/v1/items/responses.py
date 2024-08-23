from pydantic import BaseModel

from app.api.v1.offers.responses import ShortOfferResponseModel
from app.models.items import OffersDTO


class Meta(BaseModel):
    page: int
    total_items: int
    total_pages: int
    items_per_page: int


class PriceResponse(BaseModel):
    fix_price: float | None = None
    from_price: float | None = None
    to_price: float | None = None
    currency: str = "RUB"


class LocationResponse(BaseModel):
    city: str
    address: str


class ItemPhotosResponse(BaseModel):
    id: int
    link: str
    index: int


class ItemShortResponse(BaseModel):
    id: int
    title: str
    status: str
    price: PriceResponse
    location: LocationResponse | None = None
    photos: list[ItemPhotosResponse]
    date_create: str


class GetItemsResponse(BaseModel):
    items: list[ItemShortResponse | None]
    meta: Meta


class ProductionTimeResponse(BaseModel):
    from_days: int | None
    to_days: int | None


class SellerResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    rating: float


class GetItemResponse(ItemShortResponse):
    description: str
    production_time: ProductionTimeResponse
    seller: SellerResponse | None = None
    clicks: int


class GetItemResponseSeller(GetItemResponse):
    offers: list[ShortOfferResponseModel | None]
