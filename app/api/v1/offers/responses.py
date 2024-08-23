from pydantic import BaseModel


class UserShortResponse(BaseModel):
    id: int
    full_name: str
    city: str
    avatar: str | None = None


class PriceResponse(BaseModel):
    fix_price: float | None = None
    from_price: float | None = None
    to_price: float | None = None
    currency: str = "RUB"


class Meta(BaseModel):
    page: int
    total_items: int
    total_pages: int
    items_per_page: int


class ItemPhotosResponse(BaseModel):
    id: int
    link: str
    index: int


class LocationResponse(BaseModel):
    city: str | None = None
    address: str | None = None


class ItemShortResponse(BaseModel):
    id: int
    title: str
    status: str | None = None
    price: PriceResponse
    location: LocationResponse | None = None
    photos: list[ItemPhotosResponse]
    date_create: str | None = None


class ShortOfferResponseModel(BaseModel):
    id: int
    from_user: UserShortResponse
    to_user: UserShortResponse
    status: "OfferStatus"
    item: ItemShortResponse | None = None
    request: None = None
    date_create: str


class GetOffersResponse(BaseModel):
    result: list[ShortOfferResponseModel]
    meta: Meta


class OfferStatus(BaseModel):
    status: str
    comment: str | None = None


class OfferDetails(BaseModel):
    price: float
    currency: str = "RUB"
    production: int | None = None
    comment: str | None = None


class GetOfferResponse(BaseModel):
    id: int
    from_user: UserShortResponse | None = None
    to_user: UserShortResponse | None = None
    status: OfferStatus
    item: ItemShortResponse | None = None
    request: None = None
    details: OfferDetails
    date_create: str


class OfferMessageResponse(BaseModel):
    id: int
    offer_id: int
    from_user: UserShortResponse
    to_user: UserShortResponse
    text: str
    is_read: bool


class GetOfferMessageResponse(BaseModel):
    messages: list[OfferMessageResponse | None]
