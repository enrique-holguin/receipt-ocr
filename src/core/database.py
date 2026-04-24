from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

_engine = create_async_engine(
    str(get_settings().database_url),
    echo=False,
    pool_pre_ping=True,
)

_async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with _async_session_factory() as session:
        yield session
