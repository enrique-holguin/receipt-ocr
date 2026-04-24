import logging
import logging.config
from typing import Any


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging.

    Args:
        level: Root log level string (DEBUG, INFO, WARNING, ERROR).
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level.upper(),
            "handlers": ["console"],
        },
        # Quiet noisy third-party loggers.
        "loggers": {
            "uvicorn.access": {"level": "WARNING"},
            "sqlalchemy.engine": {"level": "WARNING"},
        },
    }
    logging.config.dictConfig(config)
