"""
GitNova v4.2 — Async Database Client

Manages a single asyncpg connection pool shared across all FastAPI requests.
The API is read-only — workers write, the API reads.

Connection pool is initialized once on app startup via lifespan event in main.py.

Usage:
    from app.db.client import get_db
    async with get_db() as conn:
        rows = await conn.fetch("SELECT * FROM repos WHERE is_active = TRUE")
"""

import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level pool — initialized once, shared across all requests
_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    """
    Initialize the connection pool. Called once at app startup.
    Pool size: min 2, max 10 connections — appropriate for Render free tier.
    """
    global _pool
    if not settings.has_database:
        logger.warning("DATABASE_URL not set — database features will be unavailable")
        return

    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=2,
            max_size=10,
            command_timeout=30,
            statement_cache_size=0,     # Required for pgBouncer / Supabase pooler
        )
        # Verify connection
        async with _pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        logger.info("database_connected", extra={"pool_min": 2, "pool_max": 10})
    except Exception as e:
        logger.error("database_connection_failed", extra={"error": str(e)})
        _pool = None
        raise


async def close_pool() -> None:
    """Close the connection pool. Called on app shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("database_pool_closed")
        _pool = None


@asynccontextmanager
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    Async context manager that yields a database connection from the pool.

    Usage:
        async with get_db() as conn:
            result = await conn.fetch("SELECT ...")
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool not initialized. "
            "Check that DATABASE_URL is set and the app started correctly."
        )
    async with _pool.acquire() as conn:
        yield conn


def get_pool() -> asyncpg.Pool | None:
    """Return the raw pool — useful for health checks."""
    return _pool
