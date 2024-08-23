from babel.dates import format_date
from sqlalchemy import select, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, with_loader_criteria, selectinload, contains_eager

from app.api.common.responses import Category
from app.api.v1.items.requests import Location
from app.models.common import CategoryShortDTO
from app.models.items import ItemCreateDTO, ItemPriceDTO, ItemProductionDTO, ItemShortDTO, PhotosDTO, ItemFullDTO, \
    Seller, OffersDTO, OfferSenderDTO
from app.repository.models import Items, ItemsPrice, ProductionTime, ItemsCategory, ItemsPhoto, ItemsLocations, Users, \
    Offers, ItemsClicks
from app.repository.repository import BaseRepository


class ItemsRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create(self, body: ItemCreateDTO):
        item = Items(
            **body.model_dump(exclude_none=True),
        )
        self.session.add(item)
        await self.session.flush()
        item_id = item.id
        status = item.status
        return item_id, status

    async def add_price(self, item_price_info_dto: ItemPriceDTO):
        item_price = ItemsPrice(
            **item_price_info_dto.model_dump(exclude_none=True),
        )
        self.session.add(item_price)

    async def add_production_time(self, production_time_info: ItemProductionDTO):
        prod_time = ProductionTime(
            **production_time_info.model_dump(exclude_none=True),
        )
        self.session.add(prod_time)

    async def add_category(self, item_id: int, category_id: int):
        category = ItemsCategory(
            item_id=item_id,
            category_id=category_id,
        )
        self.session.add(category)

    async def get_item_creator(self, item_id: int):
        statement = select(
            Items.creator_id
        ).filter_by(
            id=item_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def delete_item(self, item_id: int):
        statement = delete(
            Items
        ).filter_by(
            id=item_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def is_exist_photo(self, index: int, item_id: int):
        statement = select(
            ItemsPhoto
        ).filter_by(
            item_id=item_id,
            index=index
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        if result is None:
            return False
        return True

    async def is_exist_photo_by_id(self, photo_id: int):
        statement = select(
            ItemsPhoto.link
        ).filter_by(
            id=photo_id
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        if result is None:
            return False
        return result

    async def add_photo(self, link: str, index: int, item_id: int):
        photo = ItemsPhoto(
            item_id=item_id,
            link=link,
            index=index,
        )
        self.session.add(photo)
        await self.session.commit()

    async def delete_photo(self, photo_id: int):
        statement = delete(
            ItemsPhoto
        ).filter_by(
            id=photo_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def add_city(self, item_id: int, location: Location):
        address = ItemsLocations(
            item_id=item_id,
            city_id=location.city_id,
            address=location.address,
        )
        self.session.add(address)

    async def get_user_items_quantity(
            self, user_id: int, query: str = None
    ):
        statement = select(
            func.count(Items.id)
        ).filter_by(
            creator_id=user_id
        )
        if query:
            statement = statement.where(
                Items.title.ilike(f"{query}%")
            )

        result = await self.session.execute(statement)
        result = result.scalar()
        return result

    async def get_user_items(
            self, user_id: int, offset: int,
            limit: int, query: str = None
    ):
        statement = select(
            Items
        ).order_by(
            Items.created_at.desc()
        ).options(
            joinedload(Items.price)
        ).options(
            joinedload(Items.photos)
        ).options(
            joinedload(Items.location)
        ).filter_by(
            creator_id=user_id
        )
        if query:
            statement = statement.where(
                Items.title.ilike(f"{query}%")
            )

        result = await self.session.execute(
            statement.offset(offset).limit(limit)
        )
        result = result.scalars().unique().all()
        if not result:
            return None
        return [
            ItemShortDTO(
                id=item.id,
                title=item.title,
                price=item.price.price,
                from_price=item.price.from_price,
                to_price=item.price.to_price,
                currency=item.price.currency,
                photos=[
                    PhotosDTO(
                        id=photo.id,
                        link=photo.link,
                        index=photo.index
                    )
                    for photo in item.photos
                ] if item.photos else [],
                status=item.status.value,
                city=item.location.city.name,
                address=item.location.address,
                date_created=format_date(
                    item.created_at, format="d MMMM y", locale="ru"
                ),
            )
            for item in result
        ]

    async def get_item(self, item_id: int) -> ItemFullDTO | None:
        statement = select(Items).filter_by(
            id=item_id
        ).options(
            joinedload(Items.price)
        ).options(
            joinedload(Items.photos)
        ).options(
            joinedload(Items.location)
        ).options(
            joinedload(Items.category)
        ).options(
            joinedload(Items.reviews)
        ).options(
            joinedload(Items.production)
        ).options(
            joinedload(Items.clicks_quantity)
        ).options(
            joinedload(Items.user)
        )

        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        else:
            item = result[0]
        return ItemFullDTO(
            id=item.id,
            title=item.title,
            price=item.price.price,
            from_price=item.price.from_price,
            to_price=item.price.to_price,
            currency=item.price.currency,
            photos=[
                PhotosDTO(
                    id=photo.id,
                    link=photo.link,
                    index=photo.index
                )
                for photo in item.photos
            ] if item.photos else [],
            status=item.status.value,
            city=item.location.city.name,
            address=item.location.address,
            date_created=format_date(item.created_at, format="d MMMM y", locale="ru"),
            from_time=item.production.from_time if item.production else None,
            to_time=item.production.to_time if item.production else None,
            description=item.description,
            category=CategoryShortDTO(
                id=item.category.category.id,
                type=item.category.category.type.value,
                value=item.category.category.value
            ),
            seller=Seller(
                id=item.user.id,
                name=item.user.full_name,
                rating=item.user.rating,
                avatar=item.user.avatar.link if item.user.avatar is not None else None,
            ),
            clicks=len(item.clicks_quantity)
        )

    async def get_seller_offers_for_item(self, user_id: int, item_id: int) -> list[OffersDTO | None]:
        statement = select(
            Offers
        ).where(
            and_(
                Offers.item_id == item_id,
                Offers.to_user_id == user_id
            )
        ).order_by(
            Offers.created_at.desc()
        ).options(
            joinedload(Offers.from_user)
        )

        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return []
        return [
            OffersDTO(
                id=offer.id,
                request_id=offer.request_id,
                item_id=offer.item_id,
                from_user=OfferSenderDTO(
                    id=offer.from_user.id,
                    full_name=offer.from_user.full_name,
                    city=offer.from_user.city,
                    avatar=offer.from_user.avatar.link
                ),
                status=offer.status.value,
                created_at=offer.created_at
            )
            for offer in result
        ]

    async def add_click(self, item_id: int, user_id: int):
        click = ItemsClicks(
            item_id=item_id,
            user_id=user_id
        )
        self.session.add(click)
        await self.session.commit()

