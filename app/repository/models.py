import datetime
import enum
import uuid
from typing import Annotated

from sqlalchemy import BigInteger, TIMESTAMP, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

from app.repository.session import engine
from app.utils.types import TypesOfUser, ContactType, LegalFormat, ItemType, OrdersStatus

INT_PK = Annotated[
    int, mapped_column(BigInteger, autoincrement=True, primary_key=True)
]
CREATED_AT = Annotated[datetime.datetime, mapped_column(TIMESTAMP, default=datetime.datetime.utcnow)]
UPDATED_AT = Annotated[datetime.datetime, mapped_column(TIMESTAMP, default=datetime.datetime.utcnow,
                                                        onupdate=datetime.datetime.utcnow)]


class Base(DeclarativeBase):
    ...


class FederalDistricts(Base):
    __tablename__ = "federal_districts"

    id: Mapped[INT_PK]
    name: Mapped[str] = mapped_column(String(255))

    regions: Mapped[list["Regions"]] = relationship(
        back_populates="federal_district",
    )

    cities: Mapped[list["Cities"]] = relationship(
        back_populates="federal_district",
    )


class Regions(Base):
    __tablename__ = "regions"

    id: Mapped[INT_PK]
    name: Mapped[str] = mapped_column(String(255))
    federal_district_id: Mapped[int] = mapped_column(ForeignKey("federal_districts.id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(default=False)

    federal_district: Mapped[FederalDistricts] = relationship(
        back_populates="regions"
    )

    cities: Mapped[list["Cities"]] = relationship(
        back_populates="regions",
    )


class Cities(Base):
    __tablename__ = 'cities'

    id: Mapped[INT_PK]
    name: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"))
    federal_district_id = mapped_column(ForeignKey("federal_districts.id"))

    users: Mapped[list["UsersCities"]] = relationship(
        back_populates="city"
    )

    legal_address: Mapped[list["LegalAddress"]] = relationship(
        back_populates="city"
    )

    regions: Mapped[Regions] = relationship(
        back_populates="cities"
    )

    federal_district: Mapped[FederalDistricts] = relationship(
        back_populates="cities"
    )


class Users(Base):
    __tablename__ = "users"

    id: Mapped[INT_PK]
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    middle_name: Mapped[str] = mapped_column(String(255), nullable=True)
    type: Mapped[TypesOfUser] = mapped_column(nullable=True)
    full_filled: Mapped[bool] = mapped_column(default=False)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    user_city: Mapped["UsersCities"] = relationship(
        back_populates="user"
    )

    avatar: Mapped["UserAvatar"] = relationship(
        back_populates="user"
    )

    credentials: Mapped["UsersCredentials"] = relationship(
        back_populates="user"
    )

    contacts: Mapped[list["UsersContacts"]] = relationship(
        back_populates="user"
    )

    legal_info: Mapped["LegalInfo"] = relationship(
        back_populates="user"
    )

    items: Mapped[list["Items"]] = relationship(
        back_populates="user"
    )

    requests: Mapped[list["Requests"]] = relationship(
        back_populates="user"
    )

    offer_sender: Mapped["Offers"] = relationship(
        back_populates="from_user",
        foreign_keys="Offers.from_user_id",
    )

    offer_receiver: Mapped["Offers"] = relationship(
        back_populates="to_user",
        foreign_keys="Offers.to_user_id",
    )

    sender: Mapped["OffersTreads"] = relationship(
        back_populates="from_user",
        foreign_keys="OffersTreads.from_user_id",
    )

    receiver: Mapped["OffersTreads"] = relationship(
        back_populates="to_user",
        foreign_keys="OffersTreads.to_user_id",
    )

    @property
    def city(self):
        return self.user_city.city.name


class UsersCities(Base):
    __tablename__ = 'users_cities'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True)

    city: Mapped[Cities] = relationship(
        back_populates="users",
    )

    user: Mapped[Users] = relationship(
        back_populates="user_city",
    )


class UsersCredentials(Base):
    __tablename__ = 'user_credentials'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[UPDATED_AT]

    user: Mapped[Users] = relationship(
        back_populates="credentials"
    )


class UsersContacts(Base):
    __tablename__ = 'users_contacts'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[ContactType]
    value: Mapped[str] = mapped_column(String(255))
    is_hidden: Mapped[bool] = mapped_column(default=False)

    user: Mapped[Users] = relationship(
        back_populates="contacts"
    )


class UserAvatar(Base):
    __tablename__ = 'user_avatar'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    link: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped[Users] = relationship(
        back_populates="avatar"
    )


class LegalInfo(Base):
    __tablename__ = 'legal_info'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[LegalFormat]
    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    inn: Mapped[str] = mapped_column(String(255), nullable=True)
    ogrn: Mapped[str] = mapped_column(String(255), nullable=True)
    ogrnip: Mapped[str] = mapped_column(String(255), nullable=True)
    kpp: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped[Users] = relationship(
        back_populates="legal_info"
    )

    address: Mapped["LegalAddress"] = relationship(
        back_populates="legal_info"
    )


class LegalAddress(Base):
    __tablename__ = 'legal_address'

    id: Mapped[INT_PK]
    legal_card_id: Mapped[int] = mapped_column(ForeignKey('legal_info.id', ondelete="CASCADE"))
    city_id: Mapped[int] = mapped_column(ForeignKey('cities.id', ondelete="CASCADE"))
    postal_code: Mapped[int] = mapped_column(nullable=True)
    full_address: Mapped[str] = mapped_column(String(255), nullable=True)

    legal_info: Mapped["LegalInfo"] = relationship(
        back_populates="address"
    )

    city: Mapped[Cities] = relationship(
        back_populates="legal_address"
    )


class Categories(Base):
    __tablename__ = 'categories'

    id: Mapped[INT_PK]
    value: Mapped[str] = mapped_column(String(255))
    on_moderating: Mapped[bool] = mapped_column(default=True)
    depend_on: Mapped[int] = mapped_column()

    items: Mapped[list["ItemsCategory"]] = relationship(
        back_populates="category"
    )

    requests: Mapped[list["RequestsCategory"]] = relationship(
        back_populates="category"
    )


class Items(Base):
    __tablename__ = 'items'

    id: Mapped[INT_PK]
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    comment: Mapped[str] = mapped_column(String(255), nullable=True)
    format: Mapped[ItemType]
    is_delivered: Mapped[bool]
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    user: Mapped[Users] = relationship(
        back_populates="items"
    )

    category: Mapped["ItemsCategory"] = relationship(
        back_populates="item"
    )

    price: Mapped["ItemsPrice"] = relationship(
        back_populates="item"
    )

    photos: Mapped[list["ItemsPhoto"]] = relationship(
        back_populates="item"
    )

    production: Mapped["ProductionTime"] = relationship(
        back_populates="item"
    )


class ItemsCategory(Base):
    __tablename__ = "items_category"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)

    item: Mapped[Items] = relationship(
        back_populates="category"
    )

    category: Mapped[Categories] = relationship(
        back_populates="items"
    )


class ItemsPrice(Base):
    __tablename__ = 'items_price'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(nullable=True)
    range: Mapped[bool] = mapped_column(nullable=True)
    from_price: Mapped[float] = mapped_column(nullable=True)
    to_price: Mapped[float] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="RUB")

    item: Mapped[Items] = relationship(
        back_populates="price"
    )


class ItemsPhoto(Base):
    __tablename__ = 'items_photo'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    link: Mapped[str] = mapped_column(String(255), nullable=True)
    index: Mapped[int]

    item: Mapped[Items] = relationship(
        back_populates="photos"
    )


class ProductionTime(Base):
    __tablename__ = 'production_time'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    from_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP)
    to_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP)

    item: Mapped[Items] = relationship(
        back_populates="production"
    )


class Requests(Base):
    __tablename__ = 'requests'

    id: Mapped[INT_PK]
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    user: Mapped[Users] = relationship(
        back_populates="requests"
    )

    photos: Mapped[list["RequestsPhotos"]] = relationship(
        back_populates="request"
    )

    price: Mapped["RequestsPrice"] = relationship(
        back_populates="request"
    )

    category: Mapped["RequestsCategory"] = relationship(
        back_populates="request"
    )


class RequestsPhotos(Base):
    __tablename__ = 'requests_photos'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    link: Mapped[str] = mapped_column(String(255), nullable=True)
    index: Mapped[int]

    request: Mapped[Requests] = relationship(
        back_populates="photos"
    )


class RequestsCategory(Base):
    __tablename__ = 'request_category'

    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)

    request: Mapped[Requests] = relationship(
        back_populates="category"
    )

    category: Mapped[Categories] = relationship(
        back_populates="requests"
    )


class RequestsPrice(Base):
    __tablename__ = 'request_price'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    price: Mapped[float] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="RUB")
    range: Mapped[bool] = mapped_column(nullable=True)
    from_price: Mapped[float] = mapped_column(nullable=True)
    to_price: Mapped[float] = mapped_column(nullable=True)

    request: Mapped[Requests] = relationship(
        back_populates="price"
    )


class Offers(Base):
    __tablename__ = 'offers'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), nullable=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[OrdersStatus] = mapped_column(default=OrdersStatus.PENDING.value)
    created_at: Mapped[CREATED_AT]

    details: Mapped["OffersDetails"] = relationship(
        back_populates="offer"
    )

    threads: Mapped[list["OffersTreads"]] = relationship(
        back_populates="offer"
    )

    from_user: Mapped[Users] = relationship(
        back_populates="offer_sender",
        foreign_keys=[from_user_id]
    )

    to_user: Mapped[Users] = relationship(
        back_populates="offer_receiver",
        foreign_keys=[to_user_id]
    )


class OffersDetails(Base):
    __tablename__ = 'offers_details'

    id: Mapped[INT_PK]
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    comment: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float]
    currency: Mapped[str] = mapped_column(String(5), default="RUB")
    production: Mapped[int]
    production_unit: Mapped[str] = mapped_column(String(20))

    offer: Mapped[Offers] = relationship(
        back_populates="details"
    )


class OffersTreads(Base):
    __tablename__ = 'offers_treads'

    id: Mapped[INT_PK]
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    offer: Mapped[Offers] = relationship(
        back_populates="threads"
    )

    from_user: Mapped[Users] = relationship(
        back_populates="sender",
        foreign_keys=[from_user_id]
    )

    to_user: Mapped[Users] = relationship(
        back_populates="receiver",
        foreign_keys=[to_user_id]
    )


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
