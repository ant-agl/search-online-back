from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis, ConnectionPool

from app.repository.common.repository import CommonRepository
from app.repository.session import get_session
from app.repository.users.repository import UsersRepository
from app.services.auth.service import Authenticator
from app.services.common.service import CommonService
from app.services.users.service import UserService


async def get_common_service(session: AsyncSession = Depends(get_session)) -> CommonService:
    return CommonService(
        CommonRepository(session)
    )


async def common_routers_protecting():
    ...


class AuthTools:
    def __init__(self, user_service: UserService, auth_service: Authenticator):
        self.user_service = user_service
        self.auth_service = auth_service


async def get_auth_service(session: AsyncSession = Depends(get_session)):
    user_service = UserService(UsersRepository(session))
    return AuthTools(
        user_service,
        Authenticator(user_service)
    )


async def get_user_service(session: AsyncSession = Depends(get_session)):
    user_service = UserService(UsersRepository(session))
    return user_service


async def get_redis():
    pool = ConnectionPool.from_url('redis://localhost:6379/0')
    client = Redis.from_pool(pool)
    yield client
    await client.close()
