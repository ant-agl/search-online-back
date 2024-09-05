from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.v1.requests.requests import NewRequest
from app.repository.models import Requests, RequestsPrice, RequestsProductionTime, RequestsCategory, RequestsPhotos
from app.repository.repository import BaseRepository


class RequestsRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def add(self, user_id: int, body: NewRequest):
        request = Requests(
            creator_id=user_id,
            title=body.title,
            description=body.description,
        )
        self.session.add(request)
        await self.session.flush()
        request_id = request.id
        request_price = RequestsPrice(
            request_id=request_id,
            max_price=body.max_price,
            currency=body.currency
        )
        request_production_time = RequestsProductionTime(
            request_id=request_id,
            max_days=body.max_production_time
        )
        request_category = RequestsCategory(
            request_id=request_id,
            category_id=body.category_id
        )
        details = [request_price, request_production_time, request_category]
        for i, photo in enumerate(body.photos):
            details.append(
                RequestsPhotos(
                    request_id=request_id,
                    link=photo,
                    index=i
                )
            )

        self.session.add_all(details)
        await self.session.commit()
        return request_id

    async def get(self, request_id: int):
        statement = select(Requests).where(Requests.id == request_id).options(
            joinedload(Requests.category)
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        return result[0].to_dto()

    async def delete(self, request_id: int):
        statement = delete(
            Requests
        ).where(Requests.id == request_id)
        await self.session.execute(statement)
        await self.session.commit()

    async def get_for_seller(self, offset: int, limit: int, categories: list[int] = None):
        statement = select(
            Requests
        ).order_by(
            Requests.created_at.desc()
        )
        if categories:
            statement = statement.join(
                RequestsCategory, Requests.id == RequestsCategory.request_id
            ).filter(
                RequestsCategory.category_id.in_(categories)
            )
        result = await self.session.execute(statement.offset(offset).limit(limit))
        result = result.scalars().unique().all()
        if not result:
            return []
        return [
            rs.to_dto()
            for rs in result
        ]

    async def get_my_requests(self, user_id: int, offset: int, limit: int):
        statement = select(
            Requests
        ).filter_by(
            creator_id=user_id
        ).order_by(
            Requests.created_at.desc()
        )
        result = await self.session.execute(statement.offset(offset).limit(limit))
        result = result.scalars().unique().all()
        if not result:
            return []
        return [
            rs.to_dto()
            for rs in result
        ]

    async def total_requests_for_seller(self, categories: list[int] = None):
        statement = select(
            func.count(Requests.id),
        )
        if categories:
            statement = statement.join(
                RequestsCategory, Requests.id == RequestsCategory.request_id
            ).filter(
                RequestsCategory.category_id.in_(categories)
            )

        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def total_requests_for_user(self, user_id: int):
        statement = select(
            func.count(Requests.id)
        ).filter_by(
            creator_id=user_id
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result
