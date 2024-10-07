import datetime
from typing import Annotated

from babel.dates import format_date
from pydantic import create_model, Field, BaseModel
from sqlalchemy import BigInteger, TIMESTAMP, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

from app.models.common import CategoryDTO, CategoryShortDTO
from app.models.items import Seller, PhotosDTO, ItemFullDTO
from app.models.request import RequestDTO, RequestPhotos, RequestCategory
from app.models.users import UserShortDTO
from app.repository.session import engine
from app.utils.types import TypesOfUser, ContactType, LegalFormat, ItemType, OrdersStatus, ItemPublishStatus

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

    @property
    def model(self):
        return create_model(
            "Region",
            id=Annotated[int, Field(...)],
            name=Annotated[str, Field(...)],
            is_active=Annotated[bool, Field(...)],
            __base__=BaseModel
        ).model_validate(
            self, from_attributes=True
        ).model_dump(mode="json")


class Cities(Base):
    __tablename__ = 'cities'

    id: Mapped[INT_PK]
    name: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"))
    federal_district_id = mapped_column(ForeignKey("federal_districts.id"))

    users: Mapped[list["UsersCities"]] = relationship(
        back_populates="city"
    )

    regions: Mapped[Regions] = relationship(
        back_populates="cities"
    )

    federal_district: Mapped[FederalDistricts] = relationship(
        back_populates="cities"
    )

    items: Mapped[list["ItemsLocations"]] = relationship(
        back_populates="city"
    )


class Users(Base):
    __tablename__ = "users"

    id: Mapped[INT_PK]
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    middle_name: Mapped[str] = mapped_column(String(255), nullable=True)
    full_filled: Mapped[bool] = mapped_column(default=False)
    is_blocked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    type: Mapped[list["UsersType"]] = relationship(
        back_populates="user",
        lazy="joined",
    )

    user_city: Mapped["UsersCities"] = relationship(
        back_populates="user",
        lazy="joined"
    )

    avatar: Mapped["UserAvatar"] = relationship(
        back_populates="user",
        order_by="UserAvatar.id.desc()",
        lazy="joined"
    )

    credentials: Mapped["UsersCredentials"] = relationship(
        back_populates="user"
    )

    contacts: Mapped[list["UsersContacts"]] = relationship(
        back_populates="user",
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

    threads: Mapped[list["ThreadsParticipants"]] = relationship(
        back_populates="user",
    )

    reviews: Mapped[list["SellersReviews"]] = relationship(
        back_populates="seller",
        lazy="joined",
        foreign_keys="SellersReviews.seller_id",
    )

    my_reviews: Mapped[list["SellersReviews"]] = relationship(
        back_populates="from_user",
        foreign_keys="SellersReviews.from_user_id",
    )

    my_items_reviews: Mapped[list["ItemsReviews"]] = relationship(
        back_populates="from_user"
    )

    notifications: Mapped[list["Notifications"]] = relationship(
        back_populates="user"
    )

    main_category: Mapped["SellersCategories"] = relationship(
        back_populates="user",
    )
    favourites: Mapped["UsersFavourites"] = relationship(
        back_populates="user",
    )

    @property
    def city(self):
        return self.user_city.city.name

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @property
    def rating(self):
        if len(self.reviews) == 0:
            return 0
        return sum([rw.stars for rw in self.reviews]) // len(self.reviews)

    @property
    def types(self):
        return [
            tp.type.value
            for tp in self.type
        ]

    def to_short_dto(self):
        return UserShortDTO(
            id=self.id,
            full_name=self.full_name,
            city=self.city,
            avatar=self.avatar.link if self.avatar else None,
        )


class UsersType(Base):
    __tablename__ = "users_type"

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[TypesOfUser]

    user: Mapped[Users] = relationship(
        back_populates="type",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "type", name="users_type_user"),
    )


class UsersCities(Base):
    __tablename__ = 'users_cities'

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True)

    city: Mapped[Cities] = relationship(
        back_populates="users",
        lazy="joined"
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
    legal_address: Mapped[str] = mapped_column(String(255), nullable=True)
    inn: Mapped[str] = mapped_column(String(255), nullable=True)
    ogrn: Mapped[str] = mapped_column(String(255), nullable=True)
    ogrnip: Mapped[str] = mapped_column(String(255), nullable=True)
    kpp: Mapped[str] = mapped_column(String(255), nullable=True)

    user: Mapped[Users] = relationship(
        back_populates="legal_info"
    )


class Categories(Base):
    __tablename__ = 'categories'

    id: Mapped[INT_PK]
    type: Mapped[ItemType]
    value: Mapped[str] = mapped_column(String(255))
    on_moderating: Mapped[bool] = mapped_column(default=True)
    depend_on: Mapped[int] = mapped_column(nullable=True)
    disabled: Mapped[bool] = mapped_column(default=False)

    items: Mapped[list["ItemsCategory"]] = relationship(
        back_populates="category"
    )

    requests: Mapped[list["RequestsCategory"]] = relationship(
        back_populates="category"
    )

    sellers_categories: Mapped[list["SellersCategories"]] = relationship(
        back_populates="category"
    )

    @property
    def model(self):
        return CategoryDTO(
            id=self.id,
            type=self.type,
            value=self.value,
            on_moderating=self.on_moderating,
            depend_on=self.depend_on,
            disabled=self.disabled,
        )


class SellersCategories(Base):
    __tablename__ = 'sellers_categories'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))

    user: Mapped[Users] = relationship(
        back_populates="main_category"
    )
    category: Mapped[Categories] = relationship(
        back_populates="sellers_categories"
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
    status: Mapped[ItemPublishStatus] = mapped_column(default=ItemPublishStatus.pending.value)
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    user: Mapped[Users] = relationship(
        back_populates="items"
    )

    category: Mapped["ItemsCategory"] = relationship(
        back_populates="item",
        lazy="joined"
    )

    price: Mapped["ItemsPrice"] = relationship(
        back_populates="item",
        lazy="joined"
    )

    photos: Mapped[list["ItemsPhoto"]] = relationship(
        back_populates="item",
        lazy="joined"
    )

    production: Mapped["ProductionTime"] = relationship(
        back_populates="item",
        lazy="joined"
    )

    location: Mapped["ItemsLocations"] = relationship(
        back_populates="item",
        lazy="joined"
    )

    reviews: Mapped[list["ItemsReviews"]] = relationship(
        back_populates="item",
        lazy="joined"
    )

    clicks_quantity: Mapped[list["ItemsClicks"]] = relationship(
        back_populates="item"
    )

    offers: Mapped[list["Offers"]] = relationship(
        back_populates="item"
    )

    favourites: Mapped["UsersFavourites"] = relationship(
        back_populates="item",
    )

    @property
    def rating(self):
        if len(self.reviews) == 0:
            return 0
        return sum([r.stars for r in self.reviews]) / len(self.reviews)

    @property
    def reviews_quantity(self):
        return len(self.reviews)

    @property
    def dto_full(self):
        return ItemFullDTO(
            id=self.id,
            title=self.title,
            type=self.format,
            fix_price=self.price.fix_price,
            from_price=self.price.from_price,
            to_price=self.price.to_price,
            currency=self.price.currency,
            photos=[
                PhotosDTO(
                    id=photo.id,
                    link=photo.link,
                    index=photo.index
                )
                for photo in self.photos
            ] if self.photos else [],
            status=self.status.value,
            city=self.location.city.name,
            address=self.location.address,
            date_created=format_date(self.created_at, format="d MMMM y", locale="ru"),
            rating=self.rating,
            self=self.reviews_quantity,
            from_time=self.production.from_time if self.production else None,
            to_time=self.production.to_time if self.production else None,
            description=self.description,
            category=CategoryShortDTO(
                id=self.category.category.id,
                type=self.category.category.type.value,
                value=self.category.category.value
            ),
            seller=Seller(
                id=self.user.id,
                name=self.user.full_name,
                rating=self.user.rating,
                avatar=self.user.avatar.link if self.user.avatar is not None else None,
            ),
            clicks=len(self.clicks_quantity)
        )


class ItemsCategory(Base):
    __tablename__ = "items_category"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)

    item: Mapped[Items] = relationship(
        back_populates="category"
    )

    category: Mapped[Categories] = relationship(
        back_populates="items",
        lazy="joined"
    )


class ItemsPrice(Base):
    __tablename__ = 'items_price'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    fix_price: Mapped[float] = mapped_column(nullable=True)
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
    from_time: Mapped[int] = mapped_column(nullable=True)
    to_time: Mapped[int] = mapped_column(nullable=True)

    item: Mapped[Items] = relationship(
        back_populates="production"
    )


class ItemsLocations(Base):
    __tablename__ = 'items_locations'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="CASCADE"))
    address: Mapped[str] = mapped_column(String(255), nullable=True)

    item: Mapped[Items] = relationship(
        back_populates="location"
    )
    city: Mapped[Cities] = relationship(
        back_populates="items",
        lazy="joined"
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
        back_populates="requests",
        lazy="joined"
    )

    offers: Mapped["Offers"] = relationship(
        back_populates="request"
    )

    photos: Mapped[list["RequestsPhotos"]] = relationship(
        back_populates="request",
        lazy="joined"
    )

    price: Mapped["RequestsPrice"] = relationship(
        back_populates="request",
        lazy="joined"
    )

    category: Mapped["RequestsCategory"] = relationship(
        back_populates="request"
    )

    production_time: Mapped["RequestsProductionTime"] = relationship(
        back_populates="request",
        lazy="joined"
    )

    clicks_quantity: Mapped[list["RequestsClicks"]] = relationship(
        back_populates="request",
        lazy="joined"
    )

    def to_dto(self, extended: bool = False):
        if not extended:
            response = RequestDTO(
                id=self.id,
                creator=self.user.to_short_dto(),
                title=self.title,
                max_price=self.price.max_price,
                max_days=self.production_time.max_days,
                photos=[
                    ph.to_dto()
                    for ph in self.photos
                ] if self.photos is not None else [],
                created_at=format_date(
                    self.created_at, format="d MMMM y", locale="ru"
                )
            )
        else:
            response = RequestDTO(
                id=self.id,
                creator=self.user.to_short_dto(),
                title=self.title,
                description=self.description,
                max_price=self.price.max_price,
                max_days=self.production_time.max_days,
                photos=[
                    ph.to_dto()
                    for ph in self.photos
                ] if self.photos is not None else [],
                category=self.category.to_dto(),
                created_at=format_date(
                    self.created_at, format="d MMMM y", locale="ru"
                ),
                updated_at=format_date(
                    self.updated_at, format="d MMMM y", locale="ru"
                ),
                clicks=len(self.clicks_quantity)
            )
        return response


class RequestsPhotos(Base):
    __tablename__ = 'requests_photos'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    link: Mapped[str] = mapped_column(String(255), nullable=True)
    index: Mapped[int]

    request: Mapped[Requests] = relationship(
        back_populates="photos"
    )

    def to_dto(self):
        return RequestPhotos(
            id=self.id,
            link=self.link,
            index=self.index
        )


class RequestsCategory(Base):
    __tablename__ = 'request_category'

    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)

    request: Mapped[Requests] = relationship(
        back_populates="category"
    )

    category: Mapped[Categories] = relationship(
        back_populates="requests",
        lazy="joined"
    )

    def to_dto(self):
        return RequestCategory(
            id=self.category.id,
            value=self.category.value
        )


class RequestsPrice(Base):
    __tablename__ = 'request_price'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    max_price: Mapped[float] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="RUB")

    request: Mapped[Requests] = relationship(
        back_populates="price"
    )


class RequestsProductionTime(Base):
    __tablename__ = 'requests_production_time'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    max_days: Mapped[int] = mapped_column(nullable=True)

    request: Mapped[Requests] = relationship(
        back_populates="production_time"
    )


class Offers(Base):
    __tablename__ = 'offers'

    id: Mapped[INT_PK]
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"), nullable=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), nullable=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[OrdersStatus] = mapped_column(default=OrdersStatus.PENDING.value)
    reject_comment: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[CREATED_AT]

    item: Mapped[Items] = relationship(
        back_populates="offers"
    )

    request: Mapped["Requests"] = relationship(
        back_populates="offers"
    )

    details: Mapped["OffersDetails"] = relationship(
        back_populates="offer"
    )

    threads: Mapped[list["OffersThreads"]] = relationship(
        back_populates="offer"
    )

    from_user: Mapped[Users] = relationship(
        back_populates="offer_sender",
        foreign_keys=[from_user_id],
        lazy="joined"
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
    production: Mapped[int] = mapped_column(nullable=True)

    offer: Mapped[Offers] = relationship(
        back_populates="details"
    )


class OffersThreads(Base):
    __tablename__ = 'offers_threads'

    id: Mapped[INT_PK]
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    offer: Mapped[Offers] = relationship(
        back_populates="threads"
    )
    participants: Mapped[list["ThreadsParticipants"]] = relationship(
        back_populates="thread"
    )


class ThreadsParticipants(Base):
    __tablename__ = 'threads_participants'

    id: Mapped[INT_PK]
    thread_id: Mapped[int] = mapped_column(ForeignKey("offers_threads.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped[Users] = relationship(
        back_populates="threads"
    )

    thread: Mapped[OffersThreads] = relationship(
        back_populates="participants"
    )


class Notifications(Base):
    __tablename__ = 'notifications'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(255))
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CREATED_AT]

    user: Mapped[Users] = relationship(
        back_populates="notifications"
    )


class ItemsClicks(Base):
    __tablename__ = 'items_clicks'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[CREATED_AT]

    item: Mapped[Items] = relationship(
        back_populates="clicks_quantity",
    )

    __table_args__ = (
        UniqueConstraint(
            "item_id", "user_id",
            name="click_uniq_index",
        ),
    )


class RequestsClicks(Base):
    __tablename__ = "request_clicks"

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="CASCADE"))
    created_at: Mapped[CREATED_AT]

    request: Mapped[Requests] = relationship(
        back_populates="clicks_quantity",
    )

    __table_args__ = (
        UniqueConstraint(
            "request_id", "user_id",
            name="click_uniq_index",
        ),
    )


class SellersReviews(Base):
    __tablename__ = 'sellers_reviews'

    id: Mapped[INT_PK]
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    stars: Mapped[float]
    text: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[CREATED_AT]

    seller: Mapped[Users] = relationship(
        back_populates="reviews",
        foreign_keys=[seller_id]
    )

    from_user: Mapped[Users] = relationship(
        back_populates="my_reviews",
        foreign_keys=[from_user_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "seller_id", "from_user_id",
            name="review_uniq_index",
        ),
    )


class ItemsReviews(Base):
    __tablename__ = 'items_reviews'

    id: Mapped[INT_PK]
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    stars: Mapped[float]
    text: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[CREATED_AT]

    item: Mapped[Items] = relationship(
        back_populates="reviews",
    )

    from_user: Mapped[Users] = relationship(
        back_populates="my_items_reviews",
    )

    __table_args__ = (
        UniqueConstraint(
            "item_id", "from_user_id",
            name="review_uniq_index_items",
        ),
    )


class FAQs(Base):
    __tablename__ = 'faqs'

    id: Mapped[INT_PK]
    question: Mapped[str] = mapped_column(String(255))
    answer: Mapped[str] = mapped_column(String(255))
    

class UserReports(Base):
    __tablename__ = "users_reports"

    id: Mapped[INT_PK]
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[CREATED_AT]

    __table_args__ = (
        UniqueConstraint(
            "from_user_id", "to_user_id",
            name="review_uniq_index_items",
        ),
    )


class TechnicalSupports(Base):
    __tablename__ = 'technical_supports'

    id: Mapped[INT_PK]
    contact_email: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(String(255))
    is_resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[CREATED_AT]
    updated_at: Mapped[UPDATED_AT]

    @property
    def model(self):
        return create_model(
            "TechSupport",
            id=Annotated[int, Field(...)],
            contact_email=Annotated[str, Field(...)],
            text=Annotated[str, Field(...)],
            is_resolved=Annotated[bool, Field(...)],
            created_at=Annotated[datetime.datetime, Field(...)],
            updated_at=Annotated[datetime.datetime, Field(...)],
            __base__=BaseModel
        ).model_validate(
            self, from_attributes=True
        ).model_dump(mode="json")


class UsersFavourites(Base):
    __tablename__ = 'users_favourites'

    id: Mapped[INT_PK]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"))
    created_at: Mapped[CREATED_AT]

    user: Mapped[Users] = relationship(
        back_populates="favourites",
    )
    item: Mapped[Items] = relationship(
        back_populates="favourites",
    )


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
