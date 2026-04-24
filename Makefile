.PHONY: install run db-up db-down migrate migration test test-cov lint format typecheck check clean

UV ?= uv

install:
	$(UV) sync

run:
	$(UV) run uvicorn src.main:app --reload

db-up:
	docker compose up -d

db-down:
	docker compose down

migrate:
	$(UV) run alembic upgrade head

migration:
	@test -n "$(m)" || (echo "Usage: make migration m=\"message\"" && exit 1)
	$(UV) run alembic revision --autogenerate -m "$(m)"

test:
	$(UV) run pytest

test-cov:
	$(UV) run pytest --cov-report=html

lint:
	$(UV) run ruff check src tests

format:
	$(UV) run ruff format src tests
	$(UV) run ruff check --fix src tests

typecheck:
	$(UV) run mypy src

check: lint typecheck test

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
