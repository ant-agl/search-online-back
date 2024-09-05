from pydantic import BaseModel

from app.models.items import ItemShortDTO
from app.models.request import RequestDTO
from app.models.users import UserShortDTO


class CreateOfferDTO(BaseModel):
    item_id: int | None = None
    request_id: int | None = None
    from_user_id: int
    to_user_id: int
    price: float
    currency: str = "RUB"
    production: int
    comment: str | None = None


class OfferDTO(BaseModel):
    id: int
    from_user: UserShortDTO
    to_user: UserShortDTO
    status: str
    status_comment: str | None = None
    item: ItemShortDTO | None = None
    request: RequestDTO | None = None
    price: float
    currency: str
    production: int | None = None
    comment: str | None = None
    created_at: str
