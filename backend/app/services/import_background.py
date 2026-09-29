"""Background dataset import with live progress in SQLite."""

from __future__ import annotations

import asyncio
import logging

from app.core.database import async_session
from app.services.import_service import ImportService

logger = logging.getLogger(__name__)
_running: set[str] = set()


def is_import_running(dataset_id: str) -> bool:
    return dataset_id in _running


async def finalize_import_background(dataset_id: str) -> None:
    if dataset_id in _running:
        return
    _running.add(dataset_id)
    try:
        async with async_session() as session:
            await ImportService.finalize_import(session, dataset_id)
    except Exception:
        logger.exception("Background import failed for %s", dataset_id)
        async with async_session() as session:
            from app.models.dataset import DatasetRecord

            record = await session.get(DatasetRecord, dataset_id)
            if record and record.status == "importing":
                record.status = "error"
                record.import_progress = 0
                await session.commit()
    finally:
        _running.discard(dataset_id)


def schedule_finalize(dataset_id: str) -> None:
    asyncio.create_task(finalize_import_background(dataset_id))
