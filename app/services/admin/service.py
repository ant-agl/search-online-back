from app.api.admin.requests import AddFAQ
from app.api.common.responses import Category
from app.repository.admin.repository import AdminRepository
from app.services.service import BaseService


class AdminService(BaseService):

    _repository: AdminRepository

    def __init__(self, repository: AdminRepository):
        super().__init__(repository)

    class NotFound(Exception):
        def __init__(self, value):
            super().__init__(value)

    class ServiceException(Exception):
        def __init__(self, value):
            super().__init__(value)

    async def new_categories(self, cat_type: str):
        categories_list = await self._repository.get_new_categories(cat_type)

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
                for category in categories_list
                if category.depend_on == parent_id and category.on_moderating is True
            ]
            return children

        # result = build_tree()
        return categories_list

    async def del_or_confirm_category(self, category_id: int, approve: bool):
        category = await self._repository.get_category(category_id)
        if category is None:
            raise self.NotFound("Категория не найдена")

        if not category.on_moderating and not approve:
            raise self.ServiceException("Категория уже подтверждена")

        if approve:
            await self._repository.update_category(
                category_id, {
                    "on_moderating": False,
                }
            )
        else:
            await self._repository.delete_category(
                category_id
            )

        return {
            "success": True,
        }

    async def disable_enable_category(self, category_id: int, status: bool):
        category = await self._repository.get_category(category_id)
        if category is None:
            raise self.NotFound("Категория не найдена")

        if status:
            value = {
                "disabled": False,
            }
        else:
            value = {
                "disabled": True,
            }

        await self._repository.update_category(category_id, value)
        return {
            "success": True,
        }

    async def get_supports_requests(self):
        return await self._repository.get_supports()

    async def enable_disable_region(self, region_id: int, active: bool):
        region = await self._repository.get_region(region_id)

        if region is None:
            raise self.NotFound("Регион не найден")

        if active:
            value = {
                "is_active": True
            }
        else:
            value = {
                "is_active": False
            }

        await self._repository.update_region(region_id, value)
        return {
            "success": True,
        }

    async def get_regions(self):
        return await self._repository.get_regions()

    async def delete_faq(self, faq_id: int):
        await self._repository.delete_faq(faq_id)

    async def add_faq(self, body: AddFAQ):
        await self._repository.add_faq(body.question, body.answer)
        return {
            "success": True,
        }

