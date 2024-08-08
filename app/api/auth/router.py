from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.auth.requests import LoginRequest, RefreshTokenRequest
from app.api.auth.responses import LoginResponse, RefreshTokenResponse
from app.api.dependencies import get_auth_service, AuthTools
from app.api.exceptions import NotFoundApiException, BadRequestApiException, InternalServerError, ForbiddenApiException
from app.repository.users.exceptions import UserNotFoundException
from app.services.auth.exceptions import BadCredentialsException, OverdueTokenException, DamagedTokenException

router = APIRouter(
    prefix="/auth"
)


@router.post("/token", summary="Авторизация")
async def login(
        credentials: LoginRequest = Depends(),
        service: AuthTools = Depends(get_auth_service),

):
    try:
        tokens = await service.auth_service.authenticate_user(
            credentials.email, credentials.password
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
        raise InternalServerError(str(e))


@router.post("/refresh", summary="Обновление токена доступа")
async def refresh(
        token: RefreshTokenRequest = Depends(),
        service: AuthTools = Depends(get_auth_service),
):
    try:
        token = await service.auth_service.get_refresh_token(
            token.refresh_token
        )
        return RefreshTokenResponse(
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
        )
    except (OverdueTokenException, DamagedTokenException) as e:
        raise ForbiddenApiException(str(e))
    except Exception as e:
        raise InternalServerError(str(e))


@router.post("/password/repair", deprecated=True)
async def repair_password():
    ...


@router.post("/password/new", deprecated=True)
async def new_password():
    ...
