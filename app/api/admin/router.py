import logging

from fastapi import APIRouter, Depends
from watchfiles import awatch

from app.api.admin.requests import AddFAQ
from app.api.dependencies import get_admin_service
from app.api.exceptions import InternalServerError
from app.services.admin.service import AdminService
from app.utils.types import success_response, ItemType

router = APIRouter(
    prefix="/admin",
)

logger = logging.getLogger("AdminRouter")


@router.get(
    "/categories/new", summary="Посмотреть новые категории",
    status_code=200
)
async def get_new_categories(
        t: ItemType,
        service: AdminService = Depends(get_admin_service)
):
    try:
        return await service.new_categories(t.value)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/categories/{category_id}/moderate/{approve}",
    summary="Подтвердить/отклонить категорию", status_code=200
)
async def approve_reject_category(
        category_id, approve: bool,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        return await service.del_or_confirm_category(category_id, approve)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/categories/{category_id}/enable/{enable}",
    summary="Включить/отключить категорию", status_code=200
)
async def enable_disable_category(
        category_id, enable: bool,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        return await service.disable_enable_category(category_id, enable)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/items/new", summary="Новые товары/услуги",
    status_code=200
)
async def on_moderating_items(
        page: int = 1,
        limit: int = 20,
        service: AdminService = Depends(get_admin_service)
):
    try:
        return await service.get_items_on_moderating(page, limit)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/items/{item_id}/{approve}", summary="Подтвердить/отклонить товары/услуги",
    status_code=200
)
async def accept_reject_items(
        item_id: int,
        approve: bool,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        return await service.set_item_status(item_id, approve)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/block/{user_id}", summary="Заблокировать пользователя", status_code=200)
async def block_user(
        user_id: int,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        result = await service.block_user(user_id)
        return result
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/unlock/{user_id}", summary="Разблокировать пользователя", status_code=200)
async def unlock_user(
        user_id: int,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        result = await service.unlock_user(user_id)
        return result
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/regions", status_code=200, summary="Все регионы"
)
async def get_regions(
        service: AdminService = Depends(get_admin_service)
):
    try:
        return await service.get_regions()
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/regions/{region_id}/set/{active}", summary="Включить/отключить регион",
    status_code=200
)
async def set_active(
        region_id: int, active: bool,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        return await service.enable_disable_region(region_id, active)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/faq/append", summary="Добавить FAQ", status_code=200
)
async def append_faq(
        body: AddFAQ,
        service: AdminService = Depends(get_admin_service)
) -> success_response:
    try:
        return await service.add_faq(body)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/faq/{faq_id}", summary="Удалить FAQ", status_code=204
)
async def delete_faq(
        faq_id: int,
        service: AdminService = Depends(get_admin_service)
):
    try:
        await service.delete_faq(faq_id)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/supports", summary="Запросы в Тех поддержку", status_code=200
)
async def support(
        service: AdminService = Depends(get_admin_service)
):
    try:
        return await service.get_supports_requests()
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
