from babel.dates import format_date
from sqlalchemy import select, delete, func, or_, and_, union_all, literal, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, with_loader_criteria, selectinload, contains_eager

from app.api.common.responses import Category
from app.api.v1.items.requests import Location, GetCards
from app.models.common import CategoryShortDTO
from app.models.items import ItemCreateDTO, ItemPriceDTO, ItemProductionDTO, ItemShortDTO, PhotosDTO, ItemFullDTO, \
    Seller, OffersDTO, OfferSenderDTO
from app.models.common import ReviewsByStarsDTO
from app.models.users import ReviewDTO, UserShortDTO
from app.repository.models import Items, ItemsPrice, ProductionTime, ItemsCategory, ItemsPhoto, ItemsLocations, Users, \
    Offers, ItemsClicks, ItemsReviews
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
                type=item.format,
                price=item.price.fix_price,
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
                rating=item.rating,
                reviews_quantity=item.reviews_quantity
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
            type=item.format,
            fix_price=item.price.fix_price,
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
            rating=item.rating,
            reviews_quantity=item.reviews_quantity,
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

    async def get_reviews_quantity_for_user(
            self, _format: str, user_id: int | None = None, item_id: int | None = None
    ) -> int:

        condition = None

        if user_id is not None:
            condition = ItemsReviews.from_user_id == user_id
        elif item_id is not None:
            condition = ItemsReviews.item_id == item_id

        statement = select(
            func.count(ItemsReviews.id)
        ).join(
            Items
        ).filter(
            and_(
                condition,
                Items.format == _format
            )
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_grouped_reviews(
            self, _format: str, user_id: int | None = None, item_id: int | None = None
    ):
        stars_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        condition = None

        if user_id is not None:
            condition = ItemsReviews.from_user_id == user_id
        elif item_id is not None:
            condition = ItemsReviews.item_id == item_id
        stars_cte = union_all(
            *[
                select(literal(val).label(f"stars"))
                for val in stars_values
            ]
        ).cte("stars_range")

        statement = select(
            stars_cte,
            func.count(ItemsReviews.id)
        ).outerjoin(
            ItemsReviews, stars_cte.c.stars == ItemsReviews.stars
        ).group_by(
            stars_cte.c.stars
        ).order_by(
            stars_cte.c.stars.desc()
        ).join(
            Items
        ).filter(and_(
            condition,
            Items.format == _format
        ))
        result = await self.session.execute(statement)
        result = result.fetchall()
        if not result:
            return []
        return [
            ReviewsByStarsDTO(
                star=res[0],
                quantity=res[1]
            )
            for res in result
        ]

    async def get_items_reviews_by_user(
            self, offset: int, limit: int, _format: str | None = None,
            user_id: int | None = None, item_id: int | None = None
    ):
        criteria = {}
        if user_id is not None:
            criteria['from_user_id'] = user_id
        if item_id is not None:
            criteria['item_id'] = item_id

        statement = select(
            ItemsReviews
        ).filter_by(
            **criteria
        ).options(
            joinedload(ItemsReviews.from_user)
        )
        if _format is not None:
            statement = statement.join(
                Items
            ).filter(
                Items.format == _format
            )

        result = await self.session.execute(statement.offset(offset).limit(limit))
        result = result.scalars().unique().all()
        if not result:
            return []
        return [
            ReviewDTO(
                user=UserShortDTO(
                    id=review.from_user.id,
                    full_name=review.from_user.full_name,
                    city=review.from_user.city,
                    avatar=review.from_user.avatar.link if review.from_user.avatar else None,
                ),
                stars=review.stars,
                text=review.text,
                created_at=format_date(
                    review.created_at, format="d MMMM y", locale="ru"
                )
            )
            for review in result
        ]

    @staticmethod
    def statement_filter_constructor(
            body: GetCards
    ):
        filters = [
            Items.format == body.type.value,
            Items.status == "approved"
        ]
        if body.category_id is not None:
            filters.append(
                Items.category.has(ItemsCategory.category_id == body.category_id)
            )
        if body.from_days is not None:
            filters.append(
                Items.production.has(ProductionTime.from_time == body.from_days)
            )
        if body.to_days is not None:
            filters.append(
                Items.production.has(ProductionTime.to_time == body.to_days)
            )
        if body.from_price is not None:
            filters.append(
                or_(
                    Items.price.has(ItemsPrice.from_price >= body.from_price),
                    Items.price.has(ItemsPrice.fix_price >= body.from_price),
                )
            )
        if body.to_price is not None:
            filters.append(
                or_(
                    Items.price.has(ItemsPrice.to_price <= body.to_price),
                    Items.price.has(ItemsPrice.fix_price <= body.to_price),
                )
            )
        if body.city_id is not None:
            filters.append(
                Items.location.has(
                    ItemsLocations.city_id == body.city_id
                )
            )
        if body.q is not None:
            filters.append(
                Items.title.ilike(f"%{body.q}%")
            )

        return filters

    async def get_total_items_by_criteria(self, body: GetCards, offset: int, page_limit: int):
        statement = select(
            func.count(Items.id)
        )
        filters = self.statement_filter_constructor(body)

        statement = statement.filter(
            and_(*filters)
        )

        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_items_by_criteria(self, body: GetCards, offset: int, page_limit: int):
        statement = select(
            Items
        ).order_by(
            Items.created_at.desc()
        )
        filters = self.statement_filter_constructor(body)
        statement = statement.filter(
            and_(*filters)
        ).offset(offset).limit(page_limit)

        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return []
        return [
            ItemShortDTO(
                id=item.id,
                title=item.title,
                type=item.format,
                price=item.price.fix_price,
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
                rating=item.rating,
                reviews_quantity=item.reviews_quantity
            )
            for item in result
        ]

    async def update_item_info(self, item_id: int, new_data: dict):
        statement = update(
            Items
        ).filter_by(
            id=item_id,
        ).values(
            **new_data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def update_item_price(self, item_id: int, new_data: dict):
        statement = update(
            ItemsPrice
        ).filter_by(
            item_id=item_id,
        ).values(
            **new_data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def update_item_production_time(self, item_id: int, new_data: dict):
        statement = update(
            ProductionTime
        ).filter_by(
            item_id=item_id,
        ).values(
            **new_data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def update_item_location(self, item_id: int, new_data: dict):
        statement = update(
            ItemsLocations
        ).filter_by(
            item_id=item_id,
        ).values(
            **new_data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def update_category(self, item_id: int, category_id: int):
        statement = update(
            ItemsCategory
        ).filter_by(
            item_id=item_id,
        ).values(
            category_id=category_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def add_review(self, user_id: int, item_id: int, data: dict):
        review = ItemsReviews(
            item_id=item_id,
            from_user_id=user_id,
            **data
        )
        self.session.add(review)
        await self.session.flush()
        revies_id = review.id
        await self.session.commit()

    async def delete_review(self, item_id: int, user_id: int, review_id: int):
        statement = delete(
            ItemsReviews
        ).filter_by(
            item_id=item_id,
            from_user_id=user_id,
            id=review_id
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get_reviews(self, item_id: int, offset: int, page_limit: int, stars: int = None):
        statement = select(
            ItemsReviews
        ).options(
            joinedload(ItemsReviews.from_user)
        ).filter_by(
            item_id=item_id,
        )
        if stars is not None:
            statement = statement.filter_by(stars=stars)

        statement = statement.order_by(
            ItemsReviews.created_at.desc()
        ).offset(offset).limit(page_limit)

        reviews = await self.session.execute(statement)
        reviews = reviews.scalars().unique().all()
        if not reviews:
            return []
        return [
            ReviewDTO(
                user=rw.from_user.to_short_dto(),
                stars=rw.stars,
                text=rw.text,
                created_at=format_date(
                    rw.created_at, format="d MMMM y", locale="ru"
                )
            )
            for rw in reviews
        ]

    async def get_reviews_by_stars(self, item_id):
        stars_cte = union_all(
                *[
                    select(literal(val).label(f"stars"))
                    for val in [1.0, 2.0, 3.0, 4.0, 5.0]
                ]
        ).cte("stars_range")

        statement = select(
            stars_cte,
            func.count(ItemsReviews.id)
        ).outerjoin(
            ItemsReviews, stars_cte.c.stars == ItemsReviews.stars
        ).group_by(
            stars_cte.c.stars
        ).order_by(
            stars_cte.c.stars.desc()
        ).filter(
            ItemsReviews.item_id == item_id
        )
        result = await self.session.execute(statement)
        result = result.fetchall()
        if not result:
            return []
        return [
            ReviewsByStarsDTO(
                star=res[0],
                quantity=res[1]
            )
            for res in result
        ]


