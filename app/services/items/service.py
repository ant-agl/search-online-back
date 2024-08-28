import asyncio
from typing import Callable

import sqlalchemy

from app.api.v1.items.requests import CreateItem, UpdateItem, Location
from app.api.v1.items.responses import Meta, ItemShortResponse, PriceResponse, LocationResponse, ItemPhotosResponse
from app.models.items import ItemCreateDTO, ItemPriceDTO, ItemProductionDTO, ItemUpdateInfoDTO
from app.repository.items.repository import ItemsRepository
from app.services.common.service import CommonService
from app.services.items.exceptions import MinPriceOverMaxPriceException, CategoryOnModeratingException, \
    CategoryDisabledException, ItemNotFoundException, PhotoNotFoundException
from app.services.service import BaseService
from app.settings import settings


class ItemsService(BaseService):
    _repository: ItemsRepository

    def __init__(self, repository: ItemsRepository):
        super().__init__(repository)

    async def create_item(
            self, seller_id: int, data: CreateItem,
            common_service: CommonService
    ) -> dict[str, str]:
        item_info_main_dto = ItemCreateDTO(
            creator_id=seller_id,
            title=data.title,
            description=data.description,
            comment=data.comment,
            format=data.type.value,
            is_delivered=data.is_delivered
        )
        item_id, status = await self._repository.create(
            item_info_main_dto
        )

        coroutines = []

        category, _ = await asyncio.gather(
            common_service.check_category(
                data.category_id
            ),
            common_service.check_city(data.location.city_id)
        )
        if category.on_moderating:
            raise CategoryOnModeratingException(category.value)
        if category.disabled:
            raise CategoryDisabledException(category.value)

        coroutines.append(
            self._repository.add_city(
                item_id, data.location
            )
        )

        coroutines.append(
            self._repository.add_category(
                item_id, category.id
            )
        )

        item_price_info_dto = ItemPriceDTO(
            item_id=item_id,
            currency=data.price.currency,
        )
        if data.price.fix_price is None:
            item_price_info_dto.range = True
            item_price_info_dto.from_price = data.price.min_price
            item_price_info_dto.to_price = data.price.max_price
            if not (
                item_price_info_dto.from_price
                < item_price_info_dto.to_price
            ):
                await self.rollback()
                raise MinPriceOverMaxPriceException()
        else:
            item_price_info_dto.price = data.price.fix_price

        coroutines.append(
            self._repository.add_price(
                item_price_info_dto
            )
        )

        if data.production_time is not None:
            production_time = ItemProductionDTO(
                item_id=item_id,
                from_time=data.production_time.from_time,
                to_time=data.production_time.to_time,
            )
            coroutines.append(
                self._repository.add_production_time(
                    production_time
                )
            )

        try:
            await asyncio.gather(*coroutines)
            await self.commit()
            return {
                "id": item_id,
                "status": status,
            }
        except Exception as e:
            await self.rollback()
            raise e

    async def update_item(self, item_id: int, data: UpdateItem):
        item_info_update = ItemUpdateInfoDTO.model_validate(
            **data.model_dump(exclude_none=True)
        ).model_dump(exclude_none=True)

    async def delete_item(self, user_id: int, item_id: int):
        author_id = await self._repository.get_item_creator(
            item_id
        )
        if author_id is None:
            raise ItemNotFoundException(item_id)
        assert author_id == user_id
        await self._repository.delete_item(item_id)

    async def get_items(self, ):
        ...

    async def get_item(self, item_id):
        ...

    async def add_photo(
            self, user_id: int,
            item_id: int, index: int,
            linker: Callable[[str], str]
    ):
        author_id = await self._repository.get_item_creator(
            item_id
        )
        if author_id is None:
            raise ItemNotFoundException(item_id)
        assert author_id == user_id

        is_exist = await self._repository.is_exist_photo(
            index, item_id
        )
        if is_exist:
            return None

        key = f"{item_id}-{index}.png"
        link = linker(key)
        await self._repository.add_photo(
            link, index, item_id
        )
        return link

    async def delete_photo(self, user_id, item_id, photo_id):
        author_id, link = await asyncio.gather(
            self._repository.get_item_creator(item_id),
            self._repository.is_exist_photo_by_id(photo_id)
        )
        if author_id is None:
            raise ItemNotFoundException(item_id)
        if not link:
            raise PhotoNotFoundException()
        assert author_id == user_id

        await self._repository.delete_photo(photo_id)
        return link.replace(
            f"{settings.S3_PUBLIC_URL}/", ""
        )

    async def get_my_items(
            self, user_id: int, page: int,
            page_limit: int, query: str = None,
       ):
        offset = (page - 1) * page_limit

        total = self._repository.get_user_items_quantity(
            user_id, query
        )
        result = self._repository.get_user_items(
            user_id, offset, page_limit, query
        )

        result, total = await asyncio.gather(
            result, total
        )

        meta = Meta(
            page=page,
            total_items=total,
            total_pages=(total + page_limit - 1) // page_limit,
            items_per_page=page_limit,
        )
        if result is not None:
            result = [
                ItemShortResponse(
                    id=item.id,
                    title=item.title,
                    type=item.type,
                    status=item.status,
                    price=PriceResponse(
                        fix_price=item.price,
                        from_price=item.from_price,
                        to_price=item.to_price,
                        currency=item.currency
                    ),
                    location=LocationResponse(
                        city=item.city,
                        address=item.address
                    ),
                    photos=[
                        ItemPhotosResponse.model_validate(photo, from_attributes=True)
                        for photo in item.photos
                    ] if item.photos else [],
                    date_create=item.date_created
                )
                for item in result
            ]
        else:
            result = []

        return result, meta

    async def get_item_by_id(self, item_id: int, user_id: int = None):
        if user_id is not None:
            author_id = await self._repository.get_item_creator(item_id)
            if author_id is None:
                raise ItemNotFoundException(item_id)
            assert author_id == user_id

        item = await self._repository.get_item(item_id)

        if item is None:
            raise ItemNotFoundException(item_id)

        if item.status in ["pending", "rejected"]:
            raise ItemNotFoundException(item_id)
        return item

    async def add_click(self, item_id: int, user_id: int):
        author_id = await self._repository.get_item_creator(item_id)
        if author_id is None:
            return
        elif author_id == user_id:
            return
        try:
            await self._repository.add_click(item_id, user_id)
            return True
        except sqlalchemy.exc.IntegrityError:
            return True

    async def check_seller_item(self, item_id: int):
        return await self._repository.get_item_creator(item_id)

    async def get_reviews_from_user(
            self, user_id: int, value: str,
            offset: int, limit: int, by_stars: int | None = None
    ):
        total_items = self._repository.get_reviews_quantity_for_user(
            user_id=user_id, _format=value
        )
        total_reviews_by_stars = self._repository.get_grouped_reviews(
            user_id=user_id, _format=value
        )
        reviews = self._repository.get_items_reviews_by_user(
            user_id=user_id, _format=value, offset=offset, limit=limit
        )
        reviews, total_items, total_reviews_by_stars = await asyncio.gather(
            reviews, total_items, total_reviews_by_stars
        )
        return reviews, total_items, total_reviews_by_stars


