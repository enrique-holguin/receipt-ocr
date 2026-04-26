"""E2E tests with real PaddleOCR — no mocks.

To add a test case:
  1. Place the Yape screenshot in tests/e2e/fixtures/images/yape/<name>.jpg
  2. Create tests/e2e/fixtures/expected/yape/<name>.json with the expected fields:
       {"document_type": "yape", "status": "processed", "amount": "50.00", ...}
     Only include fields you want asserted; missing keys are skipped.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import AsyncClient

_IMAGES_DIR = Path(__file__).parent / "fixtures" / "images" / "yape"
_EXPECTED_DIR = Path(__file__).parent / "fixtures" / "expected" / "yape"


def _discover_cases() -> list[tuple[Path, dict[str, object]]]:
    images = sorted(_IMAGES_DIR.glob("*.jpg")) + sorted(_IMAGES_DIR.glob("*.png"))
    cases = []
    for image_path in images:
        expected_path = _EXPECTED_DIR / f"{image_path.stem}.json"
        expected: dict[str, object] = {}
        if expected_path.exists():
            expected = json.loads(expected_path.read_text())
        cases.append((image_path, expected))
    return cases


_CASES = _discover_cases()


@pytest.mark.e2e
@pytest.mark.parametrize(
    "image_path, expected",
    _CASES,
    ids=[c[0].stem for c in _CASES] if _CASES else [],
)
async def test_yape_real_image(
    client: AsyncClient,
    image_path: Path,
    expected: dict[str, object],
) -> None:
    if not _CASES:
        pytest.skip(
            "No hay fixtures E2E. Agregá imágenes en tests/e2e/fixtures/images/yape/"
        )

    image_bytes = image_path.read_bytes()
    suffix = image_path.suffix.lstrip(".")
    mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"

    response = await client.post(
        "/receipts/upload",
        files={"file": (image_path.name, image_bytes, mime)},
    )

    assert response.status_code == 201
    body = response.json()

    for field, expected_value in expected.items():
        assert body.get(field) == expected_value, (
            f"Field '{field}': expected {expected_value!r}, got {body.get(field)!r}"
        )


@pytest.mark.e2e
async def test_e2e_skip_if_no_fixtures(client: AsyncClient) -> None:
    """Explicit skip when no fixtures are present — surfaces the right message."""
    if _CASES:
        pytest.skip("Fixtures present; this guard test is not needed.")
    pytest.skip(
        "No hay fixtures E2E. Agregá imágenes en tests/e2e/fixtures/images/yape/"
    )
