"""System maintenance endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.demo_service import DemoService
from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/reset-demo")
async def reset_demo(session: AsyncSession = Depends(get_db)):
    """Re-seed demo dataset (removes existing demo and re-imports)."""
    record = await DemoService.reset_demo(session)
    if not record:
        return {"ok": False, "message": "Demo seed disabled or CSV missing"}
    return {"ok": True, "dataset_id": record.id, "name": record.name}


@router.post("/reset-app-data")
async def reset_app_data(session: AsyncSession = Depends(get_db)):
    """Remove all datasets and cached files (keeps logs)."""
    return await SystemService.reset_app_data(session)
