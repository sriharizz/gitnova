"""
GitNova v4.2 — Structured JSON Logger

All logs are JSON so they're parseable by any observability tool.
Every log line includes: timestamp, level, name, message, and optional extra fields.

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("repos_scored", extra={"count": 30, "duration_ms": 4500})
"""

import logging
import sys
from pythonjsonlogger.json import JsonFormatter
from app.core.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger with JSON formatting.
    Call this at the top of each module:
        logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.propagate = False

    return logger


# Root app logger
logger = get_logger("gitnova")
