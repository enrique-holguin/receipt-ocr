# read_payments

OCR-based extraction service for Peruvian receipts (Yape, Plin, bank transfers, SUNAT boleta/factura).

Architectural principles live in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). All code in this repo must respect them.

## Stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy 2.0 (async) + asyncpg
- PostgreSQL 16 (via Docker Compose)
- Alembic (async migrations)
- Pydantic v2
- PaddleOCR (OCR engine, CPU)
- `uv` for dependency management

## Setup

```bash
git clone <repo>
cd read_payments
cp .env.example .env
docker compose up -d            # starts Postgres on :5432
uv sync                         # installs prod + dev deps
uv run alembic upgrade head     # applies migrations
uv run uvicorn src.main:app --reload
```

App will be available at http://localhost:8000. Health check: `GET /health`.

> **Note:** The first time a receipt is processed, PaddleOCR downloads its models (~50–200 MB). This happens automatically on the first request and may take a few minutes.

## Procesado de recibos

Upload a receipt image and get the extracted fields back in a single request:

```bash
# Upload a Yape screenshot — returns the parsed receipt immediately
curl -X POST http://localhost:8000/receipts/upload \
  -F "file=@yape_captura.jpg"
```

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "document_type": "yape",
  "status": "processed",
  "amount": "50.00",
  "currency": "PEN",
  "operation_code": "123456789",
  "issued_at": "2024-04-15T00:00:00",
  "recipient_name": "Carlos Ríos",
  "ocr_confidence": 0.94,
  "image_path": "uploads/3fa85f64-....jpg",
  ...
}
```

**Possible status values after upload:**
- `processed` — amount and at least one more field extracted successfully.
- `needs_review` — OCR ran but couldn't extract the amount. Check `raw_ocr_text`.
- `failed` — OCR threw an exception. Check `error_message`.

**Currently supported document types:** Yape. Other receipts are processed as `document_type=unknown` without error.

## Development

### Running tests

```bash
make test           # unit + integration (fast, default)
make test-fast      # same as above — excludes e2e
make test-e2e       # e2e tests with real PaddleOCR (requires fixtures)
make test-all       # everything
make test-cov       # also writes htmlcov/
```

Coverage is enforced at 80% globally. Integration tests use a dedicated `read_payments_test` database created automatically by the test fixtures.

#### E2E tests

E2E tests call real PaddleOCR with actual screenshots. To add a case:

1. Place the Yape screenshot in `tests/e2e/fixtures/images/yape/<name>.jpg`
2. Create `tests/e2e/fixtures/expected/yape/<name>.json` with the expected fields:
   ```json
   {"document_type": "yape", "status": "processed", "amount": "50.00"}
   ```
   Only include fields you want asserted — missing keys are skipped.
3. Run `make test-e2e`.

If the fixture directory is empty, E2E tests are skipped automatically with a clear message.

> **Note:** The first E2E run downloads PaddleOCR models, which can take several minutes.

### Quality gates

```bash
make lint           # ruff
make format         # ruff format + autofix
make typecheck      # mypy --strict
make check          # lint + typecheck + test (this is what CI runs)
```

### Pre-commit

```bash
uv run pre-commit install
```

Runs ruff, mypy and basic file checks on every commit.

### Alembic

```bash
make migration m="add_xxx"      # autogenerate a new revision
make migrate                    # apply pending revisions
```

## Project layout

```
src/
  api/          HTTP transport (routes, deps). No business logic.
  core/         Config, DB engine, logging. Single source of truth.
  models/       SQLAlchemy models + status enums.
  schemas/      Pydantic DTOs (read/write).
  repositories/ Persistence. Side effects to DB live here.
  services/     Orchestration: upload + OCR processing.
  ocr/          PaddleOCR singleton and extract_text().
  extraction/   Document classifier and per-type field extractors.
tests/
  unit/         Pure-function tests, no DB.
  integration/  Real Postgres + ASGI client (OCR mocked).
  e2e/          Real OCR on actual receipt images (opt-in).
```

## Conventions

- Pure functions by default; side effects only in `repositories/` and `services/`.
- `mypy --strict` must pass.
- No `print()` — use the logger configured in `src/core/logging.py`.
- No magic strings — constants live in a `constants.py` per layer.
- No imports between modules of the same layer.
- Adding a new document type: add entry to `DOCUMENT_KEYWORDS` in `src/extraction/classifier.py` and `EXTRACTORS` in `src/extraction/extractors/__init__.py`. No changes needed in the service or API.
