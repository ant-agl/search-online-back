import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import secrets
import time
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from redis.asyncio import Redis

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
            "id": payload.id,
            "type": payload.type,
            "full_filled": payload.full_filled,
            "iss": settings.TOKEN_ISS,
            'iat': payload.id,
            "exp": exp_time
        }
        return jwt.encode(
            to_payload, key=cls.__secret_key, algorithm=cls.__algorithm
        )

    @classmethod
    async def refresh_token(cls, user_id: int, redis: Redis) -> str:
        token = f"{secrets.token_hex(64)}.{user_id}"
        result = await redis.set(
            f"user_{user_id}_refresh", token,
            ex=datetime.timedelta(days=7),
        )
        if result:
            return token

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
        return token_data

    @classmethod
    async def get_current_user(cls, token: Annotated[str, Depends(oauth_scheme)]):
        try:
            payload = cls.validate_access_token(token)
            return TokenPayload.model_validate(payload)
        except (DamagedTokenException, OverdueTokenException, JWTError) as e:
            raise UnauthorizedApiException(str(e))

    async def authenticate_user(self, login: str, password: str, redis: Redis):
        user_from_db = await self.__user_service.get_user_password(login)
        if self.verify_password(password, user_from_db):
            user_to_token = await self.__user_service.get_user_by_email(login)
            access_token, refresh_token = await asyncio.gather(
                self.access_token(user_to_token),
                self.refresh_token(user_to_token.id, redis)
            )
            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        raise BadCredentialsException()

    async def get_refresh_token(self, token: str, redis: Redis):
        token_value, user_id = token.rsplit(".", 1)
        token_in_redis = await redis.get(
            f"user_{user_id}_refresh"
        )
        if token_in_redis is None:
            raise OverdueTokenException()

        if token_in_redis.decode() != token:
            raise DamagedTokenException()

        user_to_token = await self.__user_service.get_user_token_data_by_id(
            user_id
        )
        access_token, refresh_token = await asyncio.gather(
            self.access_token(user_to_token),
            self.refresh_token(user_to_token.id, redis)
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

