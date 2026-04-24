"""Unit tests for Settings — no DB or network required."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.core.config import Settings

_VALID_DB_URL = "postgresql+asyncpg://user:pass@localhost:5432/testdb"


def test_environment_default() -> None:
    s = Settings(_env_file=None, database_url=_VALID_DB_URL)  # type: ignore[call-arg]
    assert s.environment == "dev"


def test_uploads_dir_default() -> None:
    s = Settings(_env_file=None, database_url=_VALID_DB_URL)  # type: ignore[call-arg]
    assert s.uploads_dir == Path("uploads")


def test_max_upload_bytes_default() -> None:
    s = Settings(_env_file=None, database_url=_VALID_DB_URL)  # type: ignore[call-arg]
    assert s.max_upload_bytes == 10 * 1024 * 1024


def test_custom_max_upload_bytes() -> None:
    s = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=_VALID_DB_URL,
        max_upload_bytes=5_000_000,
    )
    assert s.max_upload_bytes == 5_000_000


def test_invalid_database_url_raises() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="not-a-valid-url")  # type: ignore[call-arg]


def test_environment_literal_validation() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url=_VALID_DB_URL, environment="staging")  # type: ignore[call-arg]
