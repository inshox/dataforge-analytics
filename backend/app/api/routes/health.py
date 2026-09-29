"""Health and system status."""

import logging
from pathlib import Path

import duckdb
import polars as pl
from fastapi import APIRouter
from sqlalchemy import text

from app.__version__ import __version__
from app.core.config import ensure_data_dirs, get_settings
from app.core.database import engine
from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


async def _database_ok() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return False


def _duckdb_ok() -> bool:
    try:
        con = duckdb.connect(database=":memory:")
        con.execute("SELECT 1")
        con.close()
        return True
    except Exception as exc:
        logger.warning("DuckDB health check failed: %s", exc)
        return False


def _polars_ok() -> bool:
    try:
        _ = pl.__version__
        return True
    except Exception:
        return False


@router.get("/health", response_model=HealthResponse)
async def health():
    settings = get_settings()
    data_dir = ensure_data_dirs(settings)
    log_file = data_dir / "logs" / "backend.log"

    return HealthResponse(
        status="ok",
        service="dataforge-api",
        version=__version__,
        database="ok" if await _database_ok() else "error",
        data_directory=str(data_dir.resolve()),
        log_file=str(log_file.resolve()) if log_file.exists() else str(log_file),
        duckdb="ok" if _duckdb_ok() else "error",
        polars="ok" if _polars_ok() else "error",
        polars_version=pl.__version__,
        duckdb_version=duckdb.__version__,
        host=settings.host,
        port=settings.port,
    )
