from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis, ConnectionPool

from app.repository.admin.repository import AdminRepository
from app.repository.common.repository import CommonRepository
from app.repository.items.repository import ItemsRepository
from app.repository.messages.repository import MessagesRepository
from app.repository.mongo.client import get_mongo
from app.repository.mongo.repository import MongoRepository
from app.repository.offers.repository import OffersRepository
from app.repository.requests.repository import RequestsRepository
from app.repository.session import get_session
from app.repository.users.repository import UsersRepository
from app.services.admin.service import AdminService
from app.services.auth.service import Authenticator
from app.services.cloud_service import CloudService
from app.services.common.service import CommonService
from app.services.items.service import ItemsService
from app.services.messages.service import MessagesService
from app.services.offers.service import OffersService
from app.services.requests.service import RequestsService
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


async def get_cloud_service():
    return CloudService()


async def get_redis():
    pool = ConnectionPool.from_url('redis://localhost:6379/0')
    client = Redis.from_pool(pool)
    yield client
    await client.close()


async def get_items_service(session: AsyncSession = Depends(get_session)):
    return ItemsService(
        ItemsRepository(session)
    )


async def get_offers_service(session: AsyncSession = Depends(get_session)):
    return OffersService(
        OffersRepository(session)
    )


async def get_requests_service(session: AsyncSession = Depends(get_session)):
    return RequestsService(
        RequestsRepository(session)
    )


async def get_messages_service(
        postgres_session: AsyncSession = Depends(get_session),
        mongo_session: AsyncIOMotorDatabase = Depends(get_mongo),
):
    return MessagesService(
        mongo_repository=MongoRepository(mongo_session),
        postgres_repository=MessagesRepository(postgres_session)
    )


async def get_admin_service(session: AsyncSession = Depends(get_session)):
    return AdminService(
        AdminRepository(session)
    )
