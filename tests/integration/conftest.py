"""Integration-level fixtures shared across integration tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_extract_text() -> Generator[MagicMock, None, None]:
    """Patch extract_text so integration tests don't invoke real PaddleOCR.

    Default return value: ("", 0.0) — empty OCR output, zero confidence.
    Individual tests can override via mock_extract_text.return_value.
    """
    with patch(
        "src.services.processing_service.extract_text",
        return_value=("", 0.0),
    ) as mock:
        yield mock
