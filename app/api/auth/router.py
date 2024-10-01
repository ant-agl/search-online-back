import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.auth.requests import LoginRequest, RefreshTokenRequest, PasswordResetRequest, NewPasswordSet
from app.api.auth.responses import LoginResponse, RefreshTokenResponse
from app.api.dependencies import get_auth_service, AuthTools, get_redis
from app.api.exceptions import NotFoundApiException, BadRequestApiException, InternalServerError, ForbiddenApiException
from app.repository.users.exceptions import UserNotFoundException
from app.services.auth.exceptions import BadCredentialsException, OverdueTokenException, DamagedTokenException
from app.services.users.exceptions import UserServiceException

router = APIRouter(
    prefix="/auth"
)
logger = logging.getLogger("AuthRouter")


@router.post("/token", summary="Авторизация")
async def login(
        credentials: LoginRequest = Depends(),
        service: AuthTools = Depends(get_auth_service),
        redis: Redis = Depends(get_redis)
) -> LoginResponse:
    try:
        tokens = await service.auth_service.authenticate_user(
            credentials.email, credentials.password, redis
        )
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except BadCredentialsException as e:
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/refresh", summary="Обновление токена доступа")
async def refresh(
        token: RefreshTokenRequest = Depends(),
        service: AuthTools = Depends(get_auth_service),
        redis: Redis = Depends(get_redis)
) -> RefreshTokenResponse:
    try:
        tokens = await service.auth_service.get_refresh_token(
            token.refresh_token, redis
        )
        return RefreshTokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )
    except (OverdueTokenException, DamagedTokenException) as e:
        raise ForbiddenApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/password/repair", status_code=204)
async def repair_password(
        body: PasswordResetRequest,
        service: AuthTools = Depends(get_auth_service),
        redis: Redis = Depends(get_redis)
):
    try:
        await service.user_service.reset_password_request(
            body.email, redis
        )
    except UserNotFoundException as e:
        raise NotFoundApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))


@router.post("/password/new", status_code=204)
async def new_password(
        body: NewPasswordSet,
        service: AuthTools = Depends(get_auth_service),
        redis: Redis = Depends(get_redis)
):
    try:
        await service.user_service.new_password_set(
            body, redis
        )
    except UserServiceException as e:
        logger.error(e)
        raise BadRequestApiException(str(e))
    except Exception as e:
        logger.exception(e)
        raise InternalServerError(str(e))

