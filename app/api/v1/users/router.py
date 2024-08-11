import logging
from typing import Union

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.dependencies import get_auth_service, AuthTools, get_user_service, get_redis, get_common_service, \
    get_cloud_service
from app.api.exceptions import BaseApiException, BadRequestApiException, ErrorResponse, InternalServerError, \
    NotFoundApiException
from app.api.v1.requests.responses import RegistryUserResponse
from app.api.v1.users.requests import RegistryUserRequest, FullRegistryUserRequest, UpdateUserRequest, Contacts, \
    UpdateContactRequest
from app.api.v1.users.responses import UserContacts
from app.models.auth import TokenPayload
from app.repository.users.exceptions import UserAlreadyExistsException, UserNotFoundException
from app.services.auth.service import Authenticator
from app.services.cloud_service import CloudService
from app.services.common.exceptions import CityNotActiveException, CityNotFoundException
from app.services.common.service import CommonService
from app.services.users.service import UserService

router = APIRouter(
    prefix="/users",
)

logger = logging.getLogger("UsersRouter")


@router.post(
    "/register", summary="Метод для быстрой регистрации",
    status_code=201, response_model=Union[RegistryUserResponse, ErrorResponse]
)
async def create_customer(
        body: RegistryUserRequest,
        service: AuthTools = Depends(get_auth_service),
        redis: Redis = Depends(get_redis)
):
    user_id: int = 0
    try:
        user_password = body.password
        body.password = service.auth_service.hash_password(
            body.password
        )
        user_id = await service.user_service.registry(body)
        tokens = await service.auth_service.authenticate_user(
            body.email, user_password, redis
        )
        return RegistryUserResponse(
            user_id=user_id,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
        )
    except UserAlreadyExistsException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        await service.user_service.drop_user(user_id)
        raise InternalServerError(str(e))


@router.post("/profile", summary="Заполнение профиля пользователя", status_code=201)
async def fill_profile(
        body: FullRegistryUserRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service),
        common: CommonService = Depends(get_common_service)
):
    if user.full_filled:
        raise BadRequestApiException(
            "Профиль для данного пользователя уже заполнен"
        )
    try:
        await common.check_city(body.city_id)
    except (CityNotActiveException, CityNotFoundException) as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
    try:
        user_id = user.id
        result = await service.fill_profile(user_id, body)
        return JSONResponse(
            content={
                "success": result
            }, status_code=201
        )
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/profile", summary="Обновление профиля пользователя",
    status_code=204
)
async def update_user_profile(
        body: UpdateUserRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service),
        common: CommonService = Depends(get_common_service)
):
    user_id = user.id
    if body.city_id is not None:
        try:
            await common.check_city(body.city_id)
        except (CityNotActiveException, CityNotFoundException) as e:
            raise BadRequestApiException(str(e))
    try:
        await service.update_profile(user_id, body)
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get("/profile")
async def get_user_profile(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    user_id = user.id
    try:
        user = await service.get_user_profile(user_id)
        return user
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/profile", summary="Удаление аккаунта",
    status_code=204
)
async def delete_customer(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    user_id = user.id
    try:
        await service.drop_user(user_id)
    except Exception as e:
        raise InternalServerError(str(e))


@router.post(
    "/profile/avatar", summary="Обновление аватара",
    status_code=204
)
async def update_avatar(
        photo: UploadFile,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service),
        cloud: CloudService = Depends(get_cloud_service)
):
    user_id = user.id
    try:
        await service.update_avatar(user_id, await photo.read(), cloud)
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.get(
    "/profile/contacts", summary="Получение контактов пользователя",
    status_code=200
)
async def get_contacts(
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    user_id = user.id
    try:
        contact = await service.get_contacts(user_id)
        return UserContacts(
            result=contact
        )
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post(
    "/profile/contact", summary="Добавление контакта",
    status_code=201
)
async def add_contact(
        body: Contacts,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    user_id = user.id
    try:
        result = await service.add_contact(user_id, body)
        return JSONResponse(
            content={
                "success": result
            }, status_code=201
        )
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.delete(
    "/profile/contact/{contact_id}", summary="Удаление контакта по ID",
    status_code=204
)
async def delete_contact(
        contact_id: int,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    user_id = user.id
    try:
        await service.delete_contacts(user_id, contact_id)
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.patch(
    "/profile/contact/{contact_id}", summary="Изменение контакта по ID",
    status_code=204
)
async def update_contact(
        contact_id: int,
        body: UpdateContactRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    user_id = user.id
    try:
        await service.update_contact(
            user_id, contact_id, body
        )
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))
