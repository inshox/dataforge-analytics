"""System-wide maintenance."""

from __future__ import annotations

import shutil

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ensure_data_dirs, get_settings
from app.core.database import init_db
from app.models.dataset import DatasetRecord, FilterPresetRecord, TableViewRecord


class SystemService:
    @staticmethod
    async def reset_app_data(session: AsyncSession) -> dict:
        settings = get_settings()
        data_dir = ensure_data_dirs(settings)

        await session.execute(delete(TableViewRecord))
        await session.execute(delete(FilterPresetRecord))
        await session.execute(delete(DatasetRecord))
        await session.commit()

        for sub in ("datasets", "uploads", "exports", "cache"):
            path = data_dir / sub
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
            path.mkdir(parents=True, exist_ok=True)

        await init_db()
        return {"ok": True, "message": "Application data reset", "data_directory": str(data_dir)}
