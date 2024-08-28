import logging

from fastapi import APIRouter

from app.api.exceptions import InternalServerError

router = APIRouter(
    prefix="/requests"
)

logger = logging.getLogger("RequestRouter")


@router.post(
    "/create", status_code=201,
    summary="Создать новый запрос"
)
async def create_request(

):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/", status_code=200,
    summary="Посмотреть все запросы для продавца"
)
async def read_requests(

):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/my", status_code=200,
    summary="Посмотреть все мои запросы"
)
async def read_requests(

):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/{request_id}", status_code=200,
    summary="Посмотреть информацию о запросе"
)
async def read_request(
        request_id: int
):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/{request_id}", status_code=200,
    summary="Изменить данные запроса"
)
async def update_request(
        request_id: int
):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/{request_id}", status_code=200,
    summary="Удалить запрос"
)
async def delete_request(
        request_id: int
):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


