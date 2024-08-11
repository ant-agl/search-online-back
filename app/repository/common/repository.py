from abc import ABC

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.common import CitiesDTO, CityExtendedDTO
from app.repository.models import Cities, Regions
from app.repository.repository import BaseRepository


class CommonRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all(
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
