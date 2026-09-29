"""Worker queue API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import WorkerJobResponse, WorkerStatsResponse, WorkerSubmitRequest
from app.services.worker_service import WorkerService

router = APIRouter(prefix="/workers", tags=["workers"])


def _to_response(job) -> WorkerJobResponse:
    return WorkerJobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.get("/stats", response_model=WorkerStatsResponse)
async def worker_stats(session: Annotated[AsyncSession, Depends(get_db)]):
    s = await WorkerService.stats(session)
    return WorkerStatsResponse(**s)


@router.get("", response_model=list[WorkerJobResponse])
async def list_workers(session: Annotated[AsyncSession, Depends(get_db)]):
    jobs = await WorkerService.list_jobs(session)
    return [_to_response(j) for j in jobs]


@router.post("", response_model=WorkerJobResponse)
async def submit_worker(
    body: WorkerSubmitRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    job = await WorkerService.submit(session, body.job_type, body.payload)
    return _to_response(job)


@router.get("/{job_id}", response_model=WorkerJobResponse)
async def get_worker(job_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    job = await WorkerService.get_job(session, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return _to_response(job)


@router.post("/{job_id}/cancel")
async def cancel_worker(job_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    ok = await WorkerService.cancel(session, job_id)
    if not ok:
        raise HTTPException(400, "Cannot cancel job")
    return {"ok": True}
