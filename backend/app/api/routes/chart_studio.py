"""Chart Studio templates API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import ChartTemplateCreate, ChartTemplateResponse
from app.services.chart_template_service import ChartTemplateService

router = APIRouter(prefix="/chart-studio", tags=["chart-studio"])


@router.get("/templates", response_model=list[ChartTemplateResponse])
async def list_templates(
    session: Annotated[AsyncSession, Depends(get_db)],
    dataset_id: str | None = None,
):
    return await ChartTemplateService.list_templates(session, dataset_id)


@router.post("/templates", response_model=ChartTemplateResponse)
async def create_template(body: ChartTemplateCreate, session: Annotated[AsyncSession, Depends(get_db)]):
    return await ChartTemplateService.create_template(session, body)


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    if not await ChartTemplateService.delete_template(session, template_id):
        raise HTTPException(404, "Template not found")
    return {"ok": True}
