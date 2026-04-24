import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import health, receipts
from src.core.config import get_settings
from src.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging("DEBUG" if settings.environment == "dev" else "INFO")
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info("startup: uploads_dir=%s env=%s", settings.uploads_dir, settings.environment)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="read_payments",
    description="OCR-based extraction service for Peruvian receipts.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(receipts.router)
