from abc import ABC

from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.common.requests import CreateCategory, TechnicalRequest
from app.models.common import CitiesDTO, CityExtendedDTO, CategoryDTO, FAQsDTO
from app.repository.models import Cities, Regions, Categories, FAQs, Users, UsersCredentials, TechnicalSupports
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

    async def get_category_status_by_id(self, category_id: int):
        statement = select(
            Categories.on_moderating
        ).filter_by(
            id=category_id,
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_category_by_id(self, category_id: int):
        statement = select(
            Categories
        ).filter_by(
            id=category_id,
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        if result is None:
            return None
        return CategoryDTO.model_validate(
            result, from_attributes=True
        )

    async def get_faqs(self):
        statement = select(FAQs)
        result = await self.session.execute(statement)
        result = result.scalars().all()
        if not result:
            return None
        return [
            FAQsDTO.model_validate(item, from_attributes=True)
            for item in result
        ]

    async def check_user(self, contact_email: str):
        statement = select(
            UsersCredentials
        ).filter_by(
            email=contact_email
        )
        result = await self.session.execute(statement)
        result = result.scalars().all()
        if not result:
            return None
        else:
            return True

    async def register_tech_request(self, body: TechnicalRequest):
        request = TechnicalSupports(
            **body.model_dump()
        )
        self.session.add(request)
        await self.session.commit()

    async def get_category_depends(self, category_ids: list[int]):
        statement = select(
            Categories
        ).where(
            or_(
                Categories.id.in_(category_ids),
                Categories.depend_on.in_(category_ids)
            )
        )
        result = await self.session.execute(statement)
        result = result.scalars().all()
        if not result:
            return None
        return [
            rs.id
            for rs in result
        ]

