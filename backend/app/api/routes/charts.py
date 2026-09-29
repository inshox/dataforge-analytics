"""Chart engine metadata."""

from fastapi import APIRouter

from app.services.chart_service import ChartService

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/types")
async def list_chart_types():
    return ChartService.list_types()
