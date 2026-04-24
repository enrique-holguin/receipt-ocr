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

## Development

### Running tests

```bash
make test           # full suite with coverage to terminal
make test-cov       # also writes htmlcov/
```

Coverage is enforced at 80% globally. Tests use a dedicated `read_payments_test` database created automatically by the test fixtures against the same Postgres container.

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
  services/     Orchestration. Side effects to disk live here.
  ocr/          (placeholder, populated in later phases)
  extractors/   (placeholder, populated in later phases)
tests/
  unit/         Pure-function tests, no DB.
  integration/  Real Postgres + ASGI client.
```

## Conventions

- Pure functions by default; side effects only in `repositories/` and `services/`.
- `mypy --strict` must pass.
- No `print()` — use the logger configured in `src/core/logging.py`.
- No magic strings — constants live in a `constants.py` per layer.
- No imports between modules of the same layer.
