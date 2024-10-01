import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, Query
from pydantic import create_model, BaseModel, Field
from starlette.responses import JSONResponse

from app.api.dependencies import get_cloud_service, get_requests_service, get_common_service, get_user_service, \
    get_offers_service
from app.api.exceptions import InternalServerError, BadRequestApiException, NotFoundApiException
from app.api.v1.requests.requests import NewRequest
from app.api.v1.requests.responses import RequestResponse, RequestsResponse
from app.models.auth import TokenPayload
from app.services.auth.service import Authenticator
from app.services.cloud_service import CloudService
from app.services.common.service import CommonService
from app.services.offers.service import OffersService
from app.services.requests.exceptions import CreateRequestException, RequestException, RequestNotFound
from app.services.requests.service import RequestsService
from app.services.users.service import UserService
from app.utils.types import success_response

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
) -> Annotated[
    JSONResponse, create_model(
        "SuccessPhotoUpload",
        success=Annotated[bool, Field(...)],
        key=Annotated[str, Field(...)],
        __base__=BaseModel
    )
]:
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
) -> Annotated[
    JSONResponse, create_model(
        "SuccessRequestCreate",
        success=Annotated[bool, Field(...)],
        request_id=Annotated[int, Field(...)],
        __base__=BaseModel
    )
]:
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
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        by_category: bool = False,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
        users_service: UserService = Depends(get_user_service),
        common_service: CommonService = Depends(get_common_service)
) -> RequestsResponse:
    try:
        return await service.get_requests_for_seller(
            user, common_service, users_service, by_category, page, limit
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/my", status_code=200,
    summary="Посмотреть все мои запросы"
)
async def read_requests(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
) -> RequestsResponse:
    try:
        return await service.requests_for_creator(
            user.id, page, limit
        )
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/{request_id}", status_code=200,
    summary="Посмотреть информацию о запросе"
)
async def read_request(
        request_id: int,
        page: int = Query(1, ge=1),
        limit: int = Query(5, ge=1),
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: RequestsService = Depends(get_requests_service),
        offer_service: OffersService = Depends(get_offers_service)
) -> Annotated[dict, RequestResponse]:
    try:
        return await service.get_request_by_id(
            request_id, user.id, offer_service,
            page, limit
        )
    except RequestException as e:
        raise BadRequestApiException(str(e))
    except RequestNotFound as e:
        raise NotFoundApiException(str(e))
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
) -> success_response:
    try:
        result = await service.delete(request_id, user.id)
        return JSONResponse(
            content={
                "success": result,
            }
        )
    except RequestException as e:
        raise BadRequestApiException(str(e))
    except RequestNotFound as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


