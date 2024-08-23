from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

from app.settings import settings

engine: AsyncEngine = create_async_engine(
    url=settings.db_dsn,
    echo=settings.DEBUG,
    pool_size=30,
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=1800,
)


async_session = async_sessionmaker(bind=engine, autoflush=False, autocommit=False)


async def get_session() -> AsyncGenerator:
    async with async_session() as session:
        yield session
        await session.close()
