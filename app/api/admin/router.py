import logging

from fastapi import APIRouter

from app.api.exceptions import InternalServerError

router = APIRouter(
    prefix="/admin",
)

logger = logging.getLogger("AdminRouter")


@router.get(
    "/categories/new", summary="Посмотреть новые категории",
    status_code=200
)
async def new_categories():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/categories/{category_id}/moderate/{approve}",
    summary="Подтвердить/отклонить категорию", status_code=200
)
async def approve_category(category_id, approve: bool):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/categories/{category_id}/enable/{enable}",
    summary="Включить/отключить категорию", status_code=200
)
async def approve_category(category_id, enable: bool):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/items/new", summary="Новые товары/услуги",
    status_code=200
)
async def new_items():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/items/{item_id}/{approve}", summary="Подтвердить/отклонить товары/услуги",
    status_code=200
)
async def new_items(
        item_id: int,
        approve: bool
):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/block/{user_id}", summary="Заблокировать пользователя", status_code=200)
async def block(user_id: int):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/unlock/{user_id}", summary="Разблокировать пользователя", status_code=200)
async def block(user_id: int):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/regions/{region_id}/set/{active}", summary="Включить/отключить регион",
    status_code=200
)
async def set_active(region_id: int, active: bool):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "faq/append", summary="Добавить FAQ", status_code=200
)
async def append_faq():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/faq/{faq_id}", summary="Удалить FAQ", status_code=200
)
async def delete_faq():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/supports", summary="Запросы в Тех поддержку", status_code=200
)
async def support():
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
