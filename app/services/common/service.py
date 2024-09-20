import copy

from app.api.common.requests import CreateCategory, TechnicalRequest
from app.api.common.responses import Category, FAQSResponse
from app.models.common import CitiesDTO
from app.repository.common.repository import CommonRepository
from app.services.common.exceptions import CityNotFoundException, CityNotActiveException, ExceedingMaxDepth, \
    CategoryNotFoundException
from app.services.service import BaseService
from app.services.users.exceptions import UserNotFoundException
from app.utils.types import ItemType


class CommonService(BaseService):
    _repository: CommonRepository

    def __init__(self, repository: CommonRepository):
        super().__init__(repository)

    async def get_all(
            self, query: str | None = None,
            offset: int | None = None, limit: int | None = None
    ) -> list[CitiesDTO]:
        return await self._repository.get_all_cities(query, offset, limit)

    async def check_city(self, city_id: int) -> bool:
        result = await self._repository.check_city_active(city_id)
        if result is None:
            raise CityNotFoundException(city_id)
        if not result.is_active:
            raise CityNotActiveException(result.name)
        return True

    async def get_category_tree(
            self, category_type: ItemType,
            on_moderating: bool = False
    ):
        categories = await self._repository.get_category_tree(
            category_type.value
        )

        def build_tree(parent_id=None):
            children = [
                Category(
                    id=category.id,
                    name=category.value,
                    children=build_tree(category.id) if category.id else [],
                    parent_id=parent_id,
                    on_moderating=category.on_moderating,
                    disabled=category.disabled
                )
                for category in categories
                if category.depend_on == parent_id and category.on_moderating == on_moderating
            ]
            return children

        result = build_tree()
        return result

    async def create_new_category(self, body: CreateCategory):

        categories = await self._repository.get_category_tree(body.type.value)

        def get_depth(category_id, depth=1):
            parent_category = next((cat for cat in categories if cat.id == category_id), None)
            if parent_category and parent_category.depend_on:
                return get_depth(parent_category.depend_on, depth + 1)
            return depth

        parent_depth = get_depth(body.depend_on)
        if parent_depth >= 5:
            raise ExceedingMaxDepth()

        new_category = await self._repository.add_category(body)
        return {
            "id": new_category,
            "status": "moderating"
        }

    async def get_new_category_status(self, category_id: int):
        category = await self._repository.get_category_status_by_id(
            category_id
        )
        if category is None:
            return "rejected"
        elif category is True:
            return "moderating"
        elif category is False:
            return "accepted"

    async def check_category(self, category_id: int):
        result = await self._repository.get_category_by_id(category_id)
        if result is None:
            raise CategoryNotFoundException(category_id)
        return result

    async def get_faqs(self):
        result = await self._repository.get_faqs()
        return FAQSResponse(
            result=result
        )

    async def create_tech_support(self, body: TechnicalRequest):
        await self._repository.register_tech_request(body)

    async def get_categories_what_depend_on(self, category_ids: list[int]):
        return await self._repository.get_category_depends(category_ids)


