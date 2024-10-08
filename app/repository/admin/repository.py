from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.repository.models import Categories, TechnicalSupports, Regions, FAQs, Users, Items
from app.repository.repository import BaseRepository


class AdminRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_new_categories(self, category_type: str):
        statement = select(
            Categories
        ).filter_by(
            type=category_type,
            on_moderating=True
        )
        categories = await self.session.execute(statement)
        categories = categories.scalars().all()
        if not categories:
            return []
        return [
            cat.model
            for cat in categories
        ]

    async def get_category(self, category_id: int):
        statement = select(
            Categories
        ).filter_by(
            id=category_id,
        )
        categories = await self.session.execute(statement)
        categories = categories.scalars().all()
        if not categories:
            return None
        return categories[0].model

    async def update_category(self, category_id: int, value: dict):
        statement = update(
            Categories
        ).filter_by(
            id=category_id,
        ).values(**value)
        await self.session.execute(statement)
        await self.session.commit()

    async def delete_category(self, category_id: int):
        statement = delete(
            Categories
        ).filter_by(
            id=category_id,
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get_supports(self):
        statement = select(
            TechnicalSupports
        ).filter_by(
            is_resolved=False
        )
        results = await self.session.execute(statement)
        results = results.scalars().all()

        if not results:
            return []

        return [
            result.model
            for result in results
        ]

    async def get_region(self, region_id: int):
        statement = select(Regions).filter_by(
            id=region_id,
        )
        regions = await self.session.execute(statement)
        regions = regions.scalars().all()
        if not regions:
            return None
        return regions[0].model

    async def update_region(self, region_id: int, value: dict):
        statement = update(
            Regions
        ).filter_by(
            id=region_id,
        ).values(**value)
        await self.session.execute(statement)
        await self.session.commit()

    async def get_regions(self):
        statement = select(Regions)
        regions = await self.session.execute(statement)
        regions = regions.scalars().all()
        if not regions:
            return []

        return [
            region.model
            for region in regions
        ]

    async def delete_faq(self, faq_id: int):
        statement = delete(FAQs).filter_by(id=faq_id)
        await self.session.execute(statement)
        await self.session.commit()

    async def add_faq(self, question: str, answer: str):
        new_faq = FAQs(
            question=question,
            answer=answer
        )
        self.session.add(new_faq)
        await self.session.commit()

    async def block_user_by_id(self, user_id: int):
        statement = update(
            Users
        ).filter_by(
            id=user_id,
        ).values(
            is_blocked=True
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def unlock_user_by_id(self, user_id: int):
        statement = update(
            Users
        ).filter_by(
            id=user_id,
        ).values(
            is_unlocked=False
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def items_on_moderating(self, offset: int, limit: int):
        statement = select(
            Items
        ).filter(
            Items.status.in_(["pending", "moderate"])
        ).offset(offset).limit(limit).options(
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
            return []
        return [
            res.dto_full
            for res in result
        ]

    async def set_publish_item_status(
            self, item_id: int, status: str
    ):
        statement = update(
            Items
        ).filter_by(
            id=item_id,
        ).values(
            status=status
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def total_items_on_moderating(self):
        statement = select(func.count(Items.id)).filter(
            Items.status.in_(["pending", "moderate"])
        )

        result = await self.session.execute(statement)
        result = result.scalar()
        if not result:
            return 0
        return result