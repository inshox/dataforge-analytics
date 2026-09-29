"""Background worker queue — imports, exports, profiling, forecasting."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.v12 import WorkerJobRecord

logger = logging.getLogger(__name__)
_running: set[str] = set()


class WorkerService:
    @staticmethod
    async def list_jobs(session: AsyncSession, limit: int = 50) -> list[WorkerJobRecord]:
        q = select(WorkerJobRecord).order_by(WorkerJobRecord.created_at.desc()).limit(limit)
        return list((await session.execute(q)).scalars().all())

    @staticmethod
    async def get_job(session: AsyncSession, job_id: str) -> WorkerJobRecord | None:
        return await session.get(WorkerJobRecord, job_id)

    @staticmethod
    async def submit(session: AsyncSession, job_type: str, payload: dict) -> WorkerJobRecord:
        job = WorkerJobRecord(
            job_type=job_type,
            status="queued",
            progress=0,
            payload_json=json.dumps(payload),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        asyncio.create_task(_run_job(job.id))
        return job

    @staticmethod
    async def cancel(session: AsyncSession, job_id: str) -> bool:
        job = await session.get(WorkerJobRecord, job_id)
        if not job or job.status in ("completed", "failed", "cancelled"):
            return False
        job.status = "cancelled"
        job.finished_at = datetime.now(timezone.utc)
        await session.commit()
        _running.discard(job_id)
        return True

    @staticmethod
    async def stats(session: AsyncSession) -> dict:
        active = await session.scalar(
            select(func.count()).select_from(WorkerJobRecord).where(
                WorkerJobRecord.status.in_(("queued", "running"))
            )
        )
        queued = await session.scalar(
            select(func.count()).select_from(WorkerJobRecord).where(WorkerJobRecord.status == "queued")
        )
        mem_mb = cpu = None
        try:
            import psutil

            p = psutil.Process()
            mem_mb = round(p.memory_info().rss / 1024 / 1024, 1)
            cpu = round(p.cpu_percent(interval=0.1), 1)
        except ImportError:
            pass
        return {"active_jobs": int(active or 0), "queued_jobs": int(queued or 0), "memory_mb": mem_mb, "cpu_percent": cpu}


async def _run_job(job_id: str) -> None:
    if job_id in _running:
        return
    _running.add(job_id)
    try:
        async with async_session() as session:
            job = await session.get(WorkerJobRecord, job_id)
            if not job or job.status == "cancelled":
                return
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            job.progress = 5
            await session.commit()

            payload = json.loads(job.payload_json or "{}")
            try:
                if job.job_type == "import":
                    from app.services.import_service import ImportService

                    dataset_id = payload["dataset_id"]
                    await _set_progress(session, job_id, 20)
                    record = await ImportService.finalize_import(session, dataset_id)
                    job.result_json = json.dumps({"dataset_id": record.id, "status": record.status})
                elif job.job_type == "forecast":
                    from app.models.schemas import ForecastRequest
                    from app.services.forecast_service import ForecastService

                    req = ForecastRequest(**payload["request"])
                    result = ForecastService.forecast(payload["dataset_id"], req)
                    job.result_json = result.model_dump_json()
                elif job.job_type == "profile":
                    from app.services.profiling_service import ProfilingService

                    profile = ProfilingService.profile_dataset(payload["dataset_id"])
                    job.result_json = profile.model_dump_json()
                elif job.job_type == "export":
                    job.result_json = json.dumps({"ok": True, "path": payload.get("path", "")})
                else:
                    raise ValueError(f"Unknown job type: {job.job_type}")

                job = await session.get(WorkerJobRecord, job_id)
                if job and job.status != "cancelled":
                    job.status = "completed"
                    job.progress = 100
                    job.finished_at = datetime.now(timezone.utc)
                    await session.commit()
            except Exception as exc:
                logger.exception("Worker job %s failed", job_id)
                job = await session.get(WorkerJobRecord, job_id)
                if job:
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        job.status = "queued"
                        job.progress = 0
                        job.error_message = str(exc)
                        await session.commit()
                        asyncio.create_task(_run_job(job_id))
                    else:
                        job.status = "failed"
                        job.error_message = str(exc)
                        job.finished_at = datetime.now(timezone.utc)
                        await session.commit()
    finally:
        _running.discard(job_id)


async def _set_progress(session: AsyncSession, job_id: str, progress: int) -> None:
    job = await session.get(WorkerJobRecord, job_id)
    if job:
        job.progress = progress
        await session.commit()
