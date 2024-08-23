import enum
from typing import Final


class TypesOfUser(enum.Enum):
    seller = "seller"
    user = "user"


class ContactType(enum.Enum):
    telegram = "telegram"
    phone = "phone"
    email = "email"
    vk = "vk"


class LegalFormat(enum.Enum):
    ooo = "ooo"
    individual = "individual"
    self = "self"
    physical = "physical"


class ItemType(enum.Enum):
    item = "item"
    service = "service"


class OrdersStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class ItemPublishStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class OffersTypes(enum.Enum):
    from_me = "from_me"
    to_me = "to_me"


STATUS_MAP: Final[dict[str, str]] = {
    "PENDING": "В обработке",
    "APPROVED": "Подтвержден",
    "PROCESSING": "Выполняется",
    "REJECTED": "Отклонен исполнителем",
    "COMPLETED": "Завершен",
}