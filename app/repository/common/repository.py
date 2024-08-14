from abc import ABC

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.common.requests import CreateCategory
from app.models.common import CitiesDTO, CityExtendedDTO, CategoryDTO
from app.repository.models import Cities, Regions, Categories
from app.repository.repository import BaseRepository
from app.utils.types import ItemType


class CommonRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all_cities(
            self, q: str | None = None,
            offset: int | None = None,
            limit: int | None = None
    ) -> list[CitiesDTO]:
        statement = select(
            Cities
        ).join(Regions).filter_by(
            is_active=True
        )
        if offset is not None:
            statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        if q is not None:
            statement = statement.where(
                Cities.name.ilike(f"{q}%")
            )

        result = await self.session.execute(statement)
        result = result.scalars().all()

        return [
            CitiesDTO.model_validate(city, from_attributes=True)
            for city in result
        ]

    async def check_city_active(self, city_id: int) -> CityExtendedDTO | None:
        statement = select(
            Cities
        ).options(joinedload(Cities.regions)).filter_by(
            id=city_id
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        city = result[0]
        return CityExtendedDTO(
            id=city.id,
            name=city.name,
            is_active=city.regions.is_active,
        )

    async def get_category_tree(
            self, category_type: str
    ) -> list[CategoryDTO]:
        statement = select(
            Categories
        ).filter_by(
            type=category_type,
        )
        result = await self.session.execute(statement)
        result = result.scalars().all()
        return [
            CategoryDTO.model_validate(category, from_attributes=True)
            for category in result
        ]

    async def add_category(self, body: CreateCategory):
        new_category = Categories(
            type=body.type,
            value=body.name,
            depend_on=body.depend_on,
            disabled=True
        )
        self.session.add(new_category)
        await self.session.flush()
        new_category_id = new_category.id
        await self.session.commit()
        return new_category_id

    async def get_category_by_status(self, category_id: int):
        statement = select(
            Categories.on_moderating
        ).filter_by(
            id=category_id,
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

