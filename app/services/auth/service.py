import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import time
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.api.exceptions import UnauthorizedApiException, NotFoundApiException
from app.models.auth import TokenPayload
from app.services.auth.exceptions import OverdueTokenException, DamagedTokenException, BadCredentialsException
from app.services.users.exceptions import UserNotFoundException
from app.services.users.service import UserService
from app.settings import settings

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class Authenticator:
    __pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    __secret_key = settings.SECRET_KEY
    __algorithm = settings.ALGORITHM
    __expiration_time = settings.EXPIRES_IN

    def __init__(self, user_service: UserService | None = None):
        self.__user_service = user_service

    @classmethod
    def hash_password(cls, password: str):
        return cls.__pwd_context.hash(password)

    @classmethod
    def verify_password(
            cls, plain_password: str, hasher_password: str
    ) -> bool:
        return cls.__pwd_context.verify(plain_password, hasher_password)

    @classmethod
    async def access_token(cls, payload: TokenPayload) -> str:
        exp_time = time.time() + (604800 * 5)  # 900
        to_payload = {
            "sub": str(payload.user_id),
            "type": payload.type,
            "full_filled": payload.full_filled,
            "iss": cls.hash_password(settings.TOKEN_ISS),
            'iat': payload.user_id,
            "exp": exp_time
        }
        return jwt.encode(
            to_payload, key=cls.__secret_key, algorithm=cls.__algorithm
        )

    @classmethod
    async def refresh_token(cls, user_id: int) -> str:
        exp_time = time.time() + 604800
        to_payload = {
            "uid": user_id,
            "exp": exp_time
        }
        json_data = json.dumps(to_payload).encode()
        encoded = base64.urlsafe_b64encode(json_data).decode()
        signature = hmac.new(
            cls.__secret_key.encode(),
            encoded.encode(), hashlib.sha256
        ).hexdigest()
        return f"{encoded}.{signature}"

    @classmethod
    def validate_access_token(cls, token: str) -> dict:
        token_data = jwt.decode(
            token, cls.__secret_key, algorithms=[cls.__algorithm]
        )
        exp_time = token_data.get("exp")
        if exp_time is None:
            raise DamagedTokenException()
        if exp_time < time.time():
            raise OverdueTokenException()
        if cls.verify_password(token_data["iss"], cls.hash_password(token_data["iss"])):
            raise DamagedTokenException()
        return token_data

    @classmethod
    async def get_current_user(cls, token: Annotated[str, Depends(oauth_scheme)]):
        try:
            payload = cls.validate_access_token(token)
            payload["sub"] = int(payload["sub"])
            return TokenPayload.model_validate(payload)
        except (DamagedTokenException, OverdueTokenException, JWTError) as e:
            raise UnauthorizedApiException(e)

    async def authenticate_user(self, login: str, password: str):
        user_from_db = await self.__user_service.get_user_password(login)
        if self.verify_password(password, user_from_db):
            user_to_token = await self.__user_service.get_user_by_email(login)
            access_token, refresh_token = await asyncio.gather(
                self.access_token(user_to_token),
                self.refresh_token(user_to_token.user_id)
            )
            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        raise BadCredentialsException()

    async def get_refresh_token(self, token: str):
        encoded, signature = token.rsplit(".", 1)
        expected_signature = hmac.new(
            self.__secret_key.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            raise DamagedTokenException()
        data = base64.urlsafe_b64decode(
            encoded.encode().decode()
        )
        data = json.loads(data)

        if data.get("exp") < time.time():
            raise OverdueTokenException()

        if data.get("uid") is None:
            raise DamagedTokenException()

        user_to_token = await self.__user_service.get_user_token_data_by_id(
            data.get("uid")
        )
        access_token, refresh_token = await asyncio.gather(
            self.access_token(user_to_token),
            self.refresh_token(user_to_token.user_id)
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

