import logging
import uuid

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from starlette.responses import JSONResponse

from app.api.dependencies import get_cloud_service, get_requests_service, get_common_service
from app.api.exceptions import InternalServerError, BadRequestApiException
from app.api.v1.requests.requests import NewRequest
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.cloud_service import CloudService
from app.services.common.service import CommonService
from app.services.requests.exceptions import CreateRequestException
from app.services.requests.service import RequestsService

router = APIRouter(
    prefix="/requests"
)

logger = logging.getLogger("RequestRouter")


@router.post(
    "/photo/upload", status_code=201,
    summary="Загрузить фото и получить ключ"
)
async def photo_upload(
        bg_tasks: BackgroundTasks,
        photo: UploadFile = File(...),
        _: TokenPayload = Depends(Authenticator.get_current_user),
        service: CloudService = Depends(get_cloud_service)
):
    try:
        key = f"{uuid.uuid4()}{_.id}.png"
        link = service.get_link(key)
        await service.session()
        bg_tasks.add_task(
            service.save_file,
            await photo.read(), key
        )
        return JSONResponse(
            content={
                "success": True,
                "key": link,
            }, status_code=201
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/create", status_code=201,
    summary="Создать новый запрос"
)
async def create_request(
        body: NewRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
        common_service: CommonService = Depends(get_common_service)
):
    try:
        request_id = await service.add_request(user, body, common_service)
        return JSONResponse(
            content={
                "success": True,
                "request_id": request_id,
            }, status_code=201
        )
    except CreateRequestException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/", status_code=200,
    summary="Посмотреть все запросы для продавца"
)
async def read_requests(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
):
    try:
        return await service.get_requests_for_seller(user)
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/my", status_code=200,
    summary="Посмотреть все мои запросы"
)
async def read_requests(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
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
        request_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/{request_id}", status_code=200,
    summary="Изменить данные запроса", deprecated=True
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
        request_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
):
    try:
        ...
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


