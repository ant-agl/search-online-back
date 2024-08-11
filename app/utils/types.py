import enum


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
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
