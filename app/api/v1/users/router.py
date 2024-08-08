from typing import Union

from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service, AuthTools, get_user_service
from app.api.exceptions import BaseApiException, BadRequestApiException, ErrorResponse, InternalServerError
from app.api.v1.requests.responses import RegistryUserResponse
from app.api.v1.users.requests import RegistryUserRequest, FullRegistryUserRequest
from app.models.auth import TokenPayload
from app.repository.users.exceptions import UserAlreadyExistsException
from app.services.auth.service import Authenticator
from app.services.users.service import UserService

router = APIRouter(
    prefix="/users",
)


@router.post(
    "/register", summary="Метод для быстрой регистрации",
    status_code=201, response_model=Union[RegistryUserResponse, ErrorResponse]
)
async def create_customer(
        body: RegistryUserRequest,
        service: AuthTools = Depends(get_auth_service)
):
    try:
        user_password = body.password
        body.password = service.auth_service.hash_password(
            body.password
        )
        user_id = await service.user_service.registry(body)
        tokens = await service.auth_service.authenticate_user(
            body.email, user_password
        )
        return RegistryUserResponse(
            user_id=user_id,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
        )
    except UserAlreadyExistsException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        raise InternalServerError(str(e))


@router.post("/profile", summary="Заполнение профиля пользователя", status_code=201)
async def fill_profile(
        body: FullRegistryUserRequest,
        user: TokenPayload = Depends(Authenticator.get_current_user),
        service: UserService = Depends(get_user_service)
):
    if user.full_filled:
        raise BadRequestApiException(
            "Профиль для данного пользователя уже заполнен"
        )
    user_id = user.id
    try:
        result = await service.fill_profile(user_id, body)
        return user_id
    except Exception as e:
        raise InternalServerError(str(e))


@router.get("/")
async def get_customer():
    ...


@router.delete("/")
async def delete_customer():
    ...


@router.patch("/")
async def update_customer():
    ...


@router.post("/address")
async def add_address():
    ...


@router.get("/address")
async def get_addresses():
    ...


@router.delete("/address/{id}")
async def delete_address():
    ...


@router.patch("/address/{id}")
async def update_address():
    ...


@router.get("/contacts")
async def get_contacts():
    ...


@router.post("/contact")
async def add_contact():
    ...


@router.delete("/contact/{id}")
async def delete_contact():
    ...


@router.patch("/contact/{id}")
async def update_contact():
    ...