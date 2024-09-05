from babel.dates import format_date
from sqlalchemy import select, Result, Sequence, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.items import ItemShortDTO, PhotosDTO, UpdateStatusDTO
from app.models.offers import CreateOfferDTO, OfferDTO
from app.models.users import UserShortDTO
from app.repository.models import Offers, OffersDetails
from app.repository.repository import BaseRepository


class OffersRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def create_offer(self, offer_data: CreateOfferDTO):
        offer = Offers(
            request_id=offer_data.request_id,
            item_id=offer_data.item_id,
            from_user_id=offer_data.from_user_id,
            to_user_id=offer_data.to_user_id,
        )
        self.session.add(offer)
        await self.session.flush()
        offer_id = offer.id
        details = OffersDetails(
            offer_id=offer_id,
            price=offer_data.price,
            currency=offer_data.currency,
            comment=offer_data.comment,
            production=offer_data.production,
        )
        self.session.add(details)
        await self.session.commit()
        return offer_id

    async def get_offers_by_criteria(self, criteria: dict[str, int], offset: int, limit: int):
        statement = select(
            Offers
        ).filter_by(
            **criteria,
        ).order_by(
            Offers.created_at.desc()
        ).options(
            joinedload(Offers.item)
        ).options(
            joinedload(Offers.to_user)
        ).options(
            joinedload(Offers.details)
        ).order_by(
            Offers.created_at.desc()
        ).offset(offset).limit(limit)
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        return [
            OfferDTO(
                id=offer.id,
                from_user=UserShortDTO(
                    id=offer.from_user.id,
                    full_name=offer.from_user.full_name,
                    city=offer.from_user.city,
                    avatar=offer.from_user.avatar.link if offer.from_user.avatar is not None else None,
                ),
                to_user=UserShortDTO(
                    id=offer.to_user.id,
                    full_name=offer.to_user.full_name,
                    city=offer.to_user.city,
                    avatar=offer.to_user.avatar.link if offer.to_user.avatar is not None else None,
                ),
                status=offer.status.value,
                status_comment=offer.reject_comment,
                item=ItemShortDTO(
                    id=offer.item.id,
                    title=offer.item.title,
                    type=offer.item.format,
                    price=offer.item.price.price,
                    from_price=offer.item.price.from_price,
                    to_price=offer.item.price.to_price,
                    currency=offer.item.price.currency,
                    photos=[
                        PhotosDTO(
                            id=photo.id,
                            link=photo.link,
                            index=photo.index
                        )
                        for photo in offer.item.photos
                    ] if offer.item.photos else [],
                ) if offer.item else None,
                request=None,  # TODO: Заполнить когда будут запросы
                price=offer.details.price,
                currency=offer.details.currency,
                production=offer.details.production,
                comment=offer.details.comment,
                created_at=format_date(
                    offer.created_at, format="d MMMM y", locale="ru"
                ),
            )
            for offer in result
        ]

    async def get_user_offers_quantity(self, criteria: dict[str, int]):
        statement = select(
            func.count(Offers.id)
        ).filter_by(
            **criteria
        )
        result = await self.session.execute(statement)
        result = result.scalar()
        return result

    async def get_offer_sender(self, offer_id: int):
        statement = select(
            Offers.from_user_id
        ).filter_by(
            id=offer_id,
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def delete(self, offer_id: int):
        statement = delete(
            Offers
        ).filter_by(
            id=offer_id,
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get(self, offer_id: int):
        statement = select(
            Offers
        ).filter_by(
            id=offer_id,
        ).options(
            joinedload(Offers.item)
        ).options(
            joinedload(Offers.request)
        ).options(
            joinedload(Offers.to_user)
        ).options(
            joinedload(Offers.details)
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        offer = result[0]
        return OfferDTO(
            id=offer.id,
            from_user=UserShortDTO(
                id=offer.from_user.id,
                full_name=offer.from_user.full_name,
                city=offer.from_user.city,
                avatar=offer.from_user.avatar.link if offer.from_user.avatar is not None else None,
            ),
            to_user=UserShortDTO(
                id=offer.to_user.id,
                full_name=offer.to_user.full_name,
                city=offer.to_user.city,
                avatar=offer.to_user.avatar.link if offer.to_user.avatar is not None else None,
            ),
            status=offer.status.value,
            status_comment=offer.reject_comment,
            item=ItemShortDTO(
                id=offer.item.id,
                title=offer.item.title,
                type=offer.item.format,
                price=offer.item.price.price,
                from_price=offer.item.price.from_price,
                to_price=offer.item.price.to_price,
                currency=offer.item.price.currency,
                photos=[
                    PhotosDTO(
                        id=photo.id,
                        link=photo.link,
                        index=photo.index
                    )
                    for photo in offer.item.photos
                ] if offer.item.photos else [],
                city=offer.item.location.city.name,
                address=offer.item.location.address
            ) if offer.item else None,
            request=offer.request.to_dto() if offer.request else None,  # TODO: Заполнить когда будут запросы
            price=offer.details.price,
            currency=offer.details.currency,
            production=offer.details.production,
            comment=offer.details.comment,
            created_at=format_date(
                offer.created_at, format="d MMMM y", locale="ru"
            )
        )

    async def update(self, offer_id: int, update_data: dict[str, str]):
        statement = update(
            Offers
        ).filter_by(
            id=offer_id,
        ).values(
            **update_data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def update_details(self, offer_id: int, update_data: dict[str, str]):
        statement = update(
            OffersDetails
        ).filter_by(
            offer_id=offer_id,
        ).values(
            **update_data
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def get_offer_receiver(self, offer_id: int):
        statement = select(
            Offers.to_user_id
        ).filter_by(
            id=offer_id,
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_offer_status(self, offer_id: int):
        statement = select(
            Offers.status
        ).filter_by(
            id=offer_id,
        )
        result = await self.session.execute(statement)
        result = result.scalar_one_or_none()
        return result

    async def get_offer_to_update_status(self, offer_id: int):
        statement = select(
            Offers
        ).filter_by(
            id=offer_id,
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return None
        offer = result[0]
        return UpdateStatusDTO(
            from_user_id=offer.from_user_id,
            to_user_id=offer.to_user_id,
            item_id=offer.item_id,
            request_id=offer.request_id,
            status=offer.status.value,
        )

    async def get_offers_by_item(self, item_id: int):
        statement = select(
            Offers
        ).filter_by(
            item_id=item_id
        ).options(
            joinedload(Offers.details)
        )
        result = await self.session.execute(statement)
        result = result.scalars().unique().all()
        if not result:
            return []