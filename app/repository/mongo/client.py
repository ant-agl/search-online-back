from motor.motor_asyncio import AsyncIOMotorClient

from app.settings import settings


async def get_mongo():
    dsn = settings.mongo_dsn
    client = AsyncIOMotorClient(dsn)
    db = client.get_database()
    try:
        yield db
    finally:
        client.close()
