"""Global fixtures shared across the entire test suite."""

from __future__ import annotations

import io
from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
import src.models.receipt  # noqa: F401 — registers Receipt in Base.metadata
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.core.config import Settings
from src.core.database import get_db
from src.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    """Settings instance pointing to the test database and a temp uploads dir."""
    uploads = tmp_path_factory.mktemp("uploads")
    base_url = str(Settings().database_url).rsplit("/", 1)[0]
    return Settings(
        database_url=f"{base_url}/read_payments_test",  # type: ignore[arg-type]
        uploads_dir=uploads,
        environment="test",
    )


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_engine(test_settings: Settings) -> AsyncIterator[AsyncEngine]:
    """Session-scoped async engine against read_payments_test.

    Uses NullPool so each connect() call creates a fresh asyncpg connection
    in the current event loop — avoids "Future attached to a different loop"
    errors when function-scoped tests run in their own loops.
    """
    base_url = str(test_settings.database_url).rsplit("/", 1)[0]
    admin_url = f"{base_url}/postgres"

    admin_engine = create_async_engine(
        admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'read_payments_test'")
        )
        if not exists:
            await conn.execute(text("CREATE DATABASE read_payments_test"))
    await admin_engine.dispose()

    engine = create_async_engine(
        str(test_settings.database_url), echo=False, poolclass=NullPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Function-scoped session wrapped in a rolled-back outer transaction.

    Any commit() inside the test releases a savepoint rather than committing
    to disk — the outer ROLLBACK at teardown discards all test data.
    """
    async with async_engine.connect() as conn:
        await conn.begin()
        async with AsyncSession(
            bind=conn,  # type: ignore[call-arg]
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as session:
            yield session
        await conn.rollback()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(
    test_settings: Settings,
    db_session: AsyncSession,
) -> AsyncIterator[AsyncClient]:
    """Async HTTP client wired to the test DB session via dependency overrides."""
    from src.api.dependencies import get_settings
    from src.main import app

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_image_png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(200, 100, 50)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def fake_image_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(50, 150, 200)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def fake_image_webp() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(100, 200, 50)).save(buf, format="WEBP")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _cleanup_uploads(test_settings: Settings) -> Iterator[None]:
    """Delete uploaded files from the test uploads dir after each test."""
    yield
    for f in test_settings.uploads_dir.iterdir():
        if f.is_file():
            f.unlink(missing_ok=True)
