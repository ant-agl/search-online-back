from pydantic import BaseModel

from app.models.common import CategoryDTO, CategoryShortDTO
from app.models.users import ContactDTO


class ItemCreateDTO(BaseModel):
    creator_id: int
    title: str
    description: str | None = None
    comment: str | None = None
    format: str
    is_delivered: bool


class ItemPriceDTO(BaseModel):
    item_id: int
    price: float | None = None
    from_price: float | None = None
    to_price: float | None = None
    currency: str = "RUB"


class ItemProductionDTO(BaseModel):
    item_id: int
    from_time: int
    to_time: int


class PhotosDTO(BaseModel):
    id: int
    link: str
    index: int


class ItemShortDTO(BaseModel):
    id: int
    title: str
    type: str
    fix_price: float | None = None
    from_price: float | None = None
    to_price: float | None = None
    currency: str = "RUB"
    photos: list[PhotosDTO | None]
    status: str | None = None
    city: str | None = None
    address: str | None = None
    date_created: str | None = None
    rating: float
    reviews_quantity: int


class Seller(BaseModel):
    id: int
    name: str
    rating: float
    avatar: str | None


class ItemFullDTO(ItemShortDTO):
    from_time: int | None = None
    to_time: int | None = None
    description: str | None = None
    seller: Seller
    category: CategoryShortDTO
    clicks: int


class ItemUpdateInfoDTO(BaseModel):
    title: str | None = None
    description: str | None = None
    comment: str | None = None
    is_delivered: bool = False


class OfferSenderDTO(BaseModel):
    id: int
    full_name: str
    city: str
    avatar: str


class OffersDTO(BaseModel):
    id: int
    request_id: int | None = None
    item_id: int
    from_user: OfferSenderDTO | None = None
    to_user: OfferSenderDTO | None = None
    status: str
    created_at: str


class UpdateStatusDTO(BaseModel):
    from_user_id: int
    to_user_id: int
    item_id: int | None
    request_id: int | None
    status: str
