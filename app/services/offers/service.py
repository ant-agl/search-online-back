import asyncio
from typing import Any

from babel.dates import format_date

from app.api.v1.offers.requests import CreateOffer, UpdateOfferStatus, UpdateOfferDetails
from app.api.v1.offers.responses import ShortOfferResponseModel, OfferStatus, Meta, UserShortResponse, \
    ItemShortResponse, PriceResponse, LocationResponse, ItemPhotosResponse, GetOfferResponse, OfferDetails
from app.models.auth import TokenPayload
from app.models.offers import CreateOfferDTO
from app.repository.offers.repository import OffersRepository
from app.services.items.service import ItemsService
from app.services.offers.exceptions import WrongOfferReceiverException, WrongOfferSenderException, \
    ItemHasAnotherOwnerException, SelfOfferException, DeleteOfferException, OfferNotFoundException, \
    OfferNotBelongYouException, WrongNewStatus, OfferAlreadyClosed, UpdateStatusException
from app.services.service import BaseService
from app.services.users.service import UserService
from app.utils.types import OrdersStatus, STATUS_MAP


class OffersService(BaseService):
    _repository: OffersRepository

    def __init__(self, repository: OffersRepository):
        super().__init__(repository)

    async def create(
            self, user: TokenPayload,
            data: CreateOffer, users_service: UserService,
            items_service: ItemsService
    ):
        if user.id == data.to_user_id:
            raise SelfOfferException()
        users_types = await users_service.get_users_types(user.id, data.to_user_id)

        if data.item_id:
            if "seller" not in users_types[data.to_user_id]:
                raise WrongOfferReceiverException()
            item_owner = await items_service.check_seller_item(
                data.item_id
            )
            if item_owner != data.to_user_id:
                raise ItemHasAnotherOwnerException()
        if data.request_id:
            if "seller" not in users_types[user.id]:
                raise WrongOfferSenderException()
            # TODO: Добавить проверку владельца запроса

        offer_data = CreateOfferDTO(
            item_id=data.item_id,
            request_id=data.request_id,
            from_user_id=user.id,
            to_user_id=data.to_user_id,
            price=data.details.price,
            currency=data.details.currency,
            production=data.details.production,
            comment=data.details.comment,
        )
        offer_id = await self._repository.create_offer(offer_data)
        return offer_id

    async def get_offers(
            self, user_id: int, value: str,
            page: int, limit: int
    ):
        key = "from_user_id" if value == "from_me" else "to_user_id"
        criteria = {
            key: user_id
        }
        return await self.get_offers_by_criteria(criteria, page, limit)

    async def delete_offer(self, offer_id: int, user_id: int):
        offer_sender = await self._repository.get_offer_sender(offer_id)
        if offer_sender is None:
            raise OfferNotFoundException(offer_id)
        if offer_sender != user_id: raise DeleteOfferException()
        receiver_id = await self._repository.get_offer_receiver(offer_id)
        await self._repository.delete(offer_id)
        return receiver_id

    async def get_offer_by_id(self, offer_id: int, user_id: int):
        offer = await self._repository.get(offer_id)
        if offer is None:
            raise OfferNotFoundException(offer_id)

        owners = [offer.from_user.id, offer.to_user.id]
        if user_id not in owners:
            raise OfferNotBelongYouException(offer_id)

        return GetOfferResponse(
            id=offer.id,
            from_user=UserShortResponse.model_validate(offer.from_user, from_attributes=True),
            to_user=UserShortResponse.model_validate(offer.to_user, from_attributes=True),
            status=OfferStatus(
                status=STATUS_MAP[offer.status],
                comment=offer.status_comment
            ),
            item=ItemShortResponse(
                id=offer.item.id,
                title=offer.item.title,
                status=offer.item.status,
                price=PriceResponse(
                    fix_price=offer.item.fix_price,
                    from_price=offer.item.from_price,
                    to_price=offer.item.to_price,
                    currency=offer.item.currency
                ).model_dump(exclude_none=True),
                location=LocationResponse(
                    city=offer.item.city,
                    address=offer.item.address
                ).model_dump(exclude_none=True),
                photos=[
                    ItemPhotosResponse.model_validate(photo, from_attributes=True)
                    for photo in offer.item.photos
                ] if offer.item.photos else [],
                date_create=offer.item.date_created
            ) if offer.item else None,
            request=offer.request if offer.request else None,
            details=OfferDetails(
                price=offer.fix_price,
                currency=offer.currency,
                production=offer.production,
                comment=offer.comment
            ),
            date_create=offer.created_at
        ).model_dump(exclude_none=True)

    async def update_offer_status(self, offer_id: int, user_id: int, value: UpdateOfferStatus):
        offer = await self._repository.get_offer_to_update_status(offer_id)
        return_val = None
        error = ""
        if offer is None:
            raise OfferNotFoundException(offer_id)
        if user_id not in [offer.from_user_id, offer.to_user_id]:
            raise OfferNotBelongYouException(offer_id)

        status_map: dict[str, int] = {
            f"{status.value}": index
            for index, status in enumerate(OrdersStatus)
        }

        if offer.status in ["COMPLETED", "REJECTED"]:
            raise OfferAlreadyClosed(offer_id)

        if value.status.value == "COMPLETED":
            if offer.item_id:
                if user_id != offer.from_user_id:
                    error = "Завершить заказ может только его создатель"
            elif offer.request_id:
                if user_id != offer.to_user_id:
                    error = "Завершить заказ может только получатель"
        elif value.status.value in ["PROCESSING", "REJECTED", "APPROVED"]:
            if offer.item_id:
                if user_id != offer.to_user_id:
                    error = "Изменить статус может только исполнитель"
            elif offer.request_id:
                if user_id != offer.from_user_id:
                    error = "Изменить статус может только исполнитель"

        if error != "":
            raise UpdateStatusException(error)

        if status_map[
            value.status.value
        ] < status_map[
            offer.status
        ]:
            raise WrongNewStatus(
                offer_id,
                value.status.value,
                offer.status
            )

        update_data = {
            "status": value.status.value,
            "reject_comment": value.comment,
        }
        await self._repository.update(offer_id, update_data)

        if offer.request_id:
            return_val = offer.to_user_id
        elif offer.item_id:
            return_val = offer.from_user_id

        return return_val

    async def update_offer_details(self, offer_id: int, user_id: int, value: UpdateOfferDetails):
        owner_id = await self._repository.get_offer_sender(offer_id)
        if owner_id is None:
            raise OfferNotFoundException(offer_id)
        if owner_id != user_id:
            raise OfferNotBelongYouException(offer_id)

        receiver_id = await self._repository.get_offer_receiver(offer_id)

        update_data = value.model_dump(exclude_none=True)
        await self._repository.update_details(offer_id, update_data)
        return receiver_id

    async def get_offers_by_criteria(
            self, criteria: dict[str, Any],
            page: int, limit: int, exclude: list = None
    ):
        offset = (page - 1) * limit

        total = await self._repository.get_user_offers_quantity(
            criteria
        )

        offers = await self._repository.get_offers_by_criteria(
            criteria, offset, limit
        )
        del offset
        meta = Meta(
            page=page,
            total_items=total,
            total_pages=(total + limit - 1) // limit,
            items_per_page=limit,
        )
        if offers is not None:
            result = [
                ShortOfferResponseModel(
                    id=offer.id,
                    from_user=UserShortResponse.model_validate(offer.from_user, from_attributes=True),
                    to_user=UserShortResponse.model_validate(offer.to_user, from_attributes=True),
                    status=OfferStatus(
                        status=STATUS_MAP[offer.status],
                        comment=offer.status_comment
                    ).model_dump(exclude_none=True),
                    item=ItemShortResponse(
                        id=offer.item.id,
                        title=offer.item.title,
                        status=offer.item.status,
                        price=PriceResponse(
                            fix_price=offer.item.fix_price,
                            from_price=offer.item.from_price,
                            to_price=offer.item.to_price,
                            currency=offer.item.currency
                        ).model_dump(exclude_none=True),
                        location=LocationResponse(
                            city=offer.item.city,
                            address=offer.item.address
                        ).model_dump(exclude_none=True),
                        photos=[
                            ItemPhotosResponse.model_validate(photo, from_attributes=True)
                            for photo in offer.item.photos
                        ] if offer.item.photos else [],
                        date_create=offer.item.date_created
                    ) if offer.item else None,
                    request=offer.request if offer.request else None,
                    date_create=offer.created_at
                ).model_dump(
                    exclude_none=True,
                    exclude=set(exclude) if exclude else None
                )
                for offer in offers
            ]
        else:
            result = []

        return result, meta

    async def offer_participants(self, offer_id: int, user_id: int):
        # participants = await asyncio.gather(
        #     self._repository.get_offer_sender(offer_id),
        #     self._repository.get_offer_receiver(offer_id)
        # )
        participants = [
            await self._repository.get_offer_sender(offer_id),
            await self._repository.get_offer_receiver(offer_id)
        ]
        if not participants:
            raise OfferNotFoundException(offer_id)
        if user_id not in participants:
            raise OfferNotBelongYouException(offer_id)

        return participants



