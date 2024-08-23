from pydantic import BaseModel, model_validator, Field

from app.api.exceptions import UnprocessableApiException
from app.utils.types import OrdersStatus


class OfferDetails(BaseModel):
    price: float = Field(gt=0)
    currency: str = "RUB"
    production: int
    comment: str | None = None


class CreateOffer(BaseModel):
    item_id: int | None = None
    request_id: int | None = None
    to_user_id: int
    details: OfferDetails

    @model_validator(mode="after")
    def validate_source(self):
        if self.item_id is None and self.request_id is None:
            raise UnprocessableApiException("Не указан источник заказа: Запрос или товар")
        return self


class UpdateOfferDetails(BaseModel):
    price: float | None = None
    production: int | None = None
    comment: str | None = None


class OfferMessage(BaseModel):
    offer_id: int
    to_user_id: int
    text: str


class UpdateOfferMessage(BaseModel):
    message_id: int
    text: str


class UpdateOfferStatus(BaseModel):
    status: OrdersStatus
    comment: str | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if self.status.value == "REJECTED" and self.comment is None:
            raise UnprocessableApiException("Для отмены заказа нужно указать причину")
        return self


