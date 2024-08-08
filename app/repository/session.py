from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import scoped_session

from app.settings import settings

engine = create_async_engine(
    url=settings.db_dsn,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)


async_session = async_sessionmaker(bind=engine, autoflush=False, autocommit=False)


async def get_session() -> AsyncGenerator:
    async with async_session() as session:
        yield session
        await session.close()
