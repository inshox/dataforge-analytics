"""Dashboard builder API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from pydantic import BaseModel

from typing import Any

from app.models.schemas import (
    DashboardCreate,
    DashboardDetail,
    DashboardDrillthroughCreate,
    DashboardDrillthroughResponse,
    DashboardDrillthroughUpdate,
    DashboardSaveBody,
    DashboardSummary,
    DashboardTemplateSummary,
    DashboardVariableCreate,
    DashboardVariableResponse,
    DashboardVariableUpdate,
)
from app.services.dashboard_drillthrough_service import DashboardDrillthroughService
from app.services.dashboard_service import DashboardService
from app.services.dashboard_template_service import DashboardTemplateService
from app.services.dashboard_filter_preset_service import DashboardFilterPresetService
from app.services.dashboard_variable_service import DashboardVariableService
from app.models.schemas import DashboardFilterPresetCreate, DashboardFilterPresetResponse

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


class InstantiateTemplateBody(BaseModel):
    dataset_id: str
    name: str | None = None


@router.get("/templates", response_model=list[DashboardTemplateSummary])
async def list_dashboard_templates():
    return DashboardTemplateService.list_templates()


@router.post("/templates/{template_id}/instantiate", response_model=DashboardDetail)
async def instantiate_template(
    template_id: str,
    body: InstantiateTemplateBody,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await DashboardTemplateService.instantiate(
            session, template_id, body.dataset_id, body.name
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("", response_model=list[DashboardSummary])
async def list_dashboards(session: Annotated[AsyncSession, Depends(get_db)]):
    return await DashboardService.list_dashboards(session)


@router.post("", response_model=DashboardDetail)
async def create_dashboard(body: DashboardCreate, session: Annotated[AsyncSession, Depends(get_db)]):
    return await DashboardService.create_dashboard(session, body)


@router.get("/{dashboard_id}/variables", response_model=list[DashboardVariableResponse])
async def list_variables(dashboard_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    return await DashboardVariableService.list_variables(session, dashboard_id)


@router.post("/{dashboard_id}/variables", response_model=DashboardVariableResponse)
async def create_variable(
    dashboard_id: str,
    body: DashboardVariableCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DashboardVariableService.create_variable(session, dashboard_id, body)


@router.patch("/{dashboard_id}/variables/{variable_id}", response_model=DashboardVariableResponse)
async def update_variable(
    dashboard_id: str,
    variable_id: str,
    body: DashboardVariableUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await DashboardVariableService.update_variable(session, dashboard_id, variable_id, body)
    if not rec:
        raise HTTPException(404, "Variable not found")
    return rec


@router.delete("/{dashboard_id}/variables/{variable_id}")
async def delete_variable(
    dashboard_id: str, variable_id: str, session: Annotated[AsyncSession, Depends(get_db)]
):
    if not await DashboardVariableService.delete_variable(session, dashboard_id, variable_id):
        raise HTTPException(404, "Variable not found")
    return {"ok": True}


class BulkVariableValues(BaseModel):
    values: dict[str, Any] = {}


@router.patch("/{dashboard_id}/variables/bulk", response_model=list[DashboardVariableResponse])
async def bulk_variable_values(
    dashboard_id: str,
    body: BulkVariableValues,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DashboardVariableService.bulk_set_current(session, dashboard_id, body.values)


@router.get("/{dashboard_id}/filter-presets", response_model=list[DashboardFilterPresetResponse])
async def list_filter_presets(
    dashboard_id: str, session: Annotated[AsyncSession, Depends(get_db)]
):
    return await DashboardFilterPresetService.list_presets(session, dashboard_id)


@router.post("/{dashboard_id}/filter-presets", response_model=DashboardFilterPresetResponse)
async def create_filter_preset(
    dashboard_id: str,
    body: DashboardFilterPresetCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DashboardFilterPresetService.create_preset(session, dashboard_id, body)


@router.delete("/{dashboard_id}/filter-presets/{preset_id}")
async def delete_filter_preset(
    dashboard_id: str, preset_id: str, session: Annotated[AsyncSession, Depends(get_db)]
):
    if not await DashboardFilterPresetService.delete_preset(session, dashboard_id, preset_id):
        raise HTTPException(404, "Preset not found")
    return {"ok": True}


@router.get("/{dashboard_id}/drillthrough", response_model=list[DashboardDrillthroughResponse])
async def list_drillthrough(dashboard_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    return await DashboardDrillthroughService.list_rules(session, dashboard_id)


@router.post("/{dashboard_id}/drillthrough", response_model=DashboardDrillthroughResponse)
async def create_drillthrough(
    dashboard_id: str,
    body: DashboardDrillthroughCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await DashboardDrillthroughService.create_rule(session, dashboard_id, body)


@router.patch("/{dashboard_id}/drillthrough/{rule_id}", response_model=DashboardDrillthroughResponse)
async def update_drillthrough(
    dashboard_id: str,
    rule_id: str,
    body: DashboardDrillthroughUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    rec = await DashboardDrillthroughService.update_rule(session, dashboard_id, rule_id, body)
    if not rec:
        raise HTTPException(404, "Rule not found")
    return rec


@router.delete("/{dashboard_id}/drillthrough/{rule_id}")
async def delete_drillthrough(
    dashboard_id: str, rule_id: str, session: Annotated[AsyncSession, Depends(get_db)]
):
    if not await DashboardDrillthroughService.delete_rule(session, dashboard_id, rule_id):
        raise HTTPException(404, "Rule not found")
    return {"ok": True}


@router.get("/{dashboard_id}", response_model=DashboardDetail)
async def get_dashboard(dashboard_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    detail = await DashboardService.get_dashboard(session, dashboard_id)
    if not detail:
        raise HTTPException(404, "Dashboard not found")
    return detail


@router.put("/{dashboard_id}", response_model=DashboardDetail)
async def save_dashboard(
    dashboard_id: str,
    body: DashboardSaveBody,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    detail = await DashboardService.update_dashboard(session, dashboard_id, body)
    if not detail:
        raise HTTPException(404, "Dashboard not found")
    return detail


@router.delete("/{dashboard_id}")
async def delete_dashboard(dashboard_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    if not await DashboardService.delete_dashboard(session, dashboard_id):
        raise HTTPException(404, "Dashboard not found")
    return {"ok": True}


@router.post("/{dashboard_id}/duplicate", response_model=DashboardDetail)
async def duplicate_dashboard(dashboard_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    detail = await DashboardService.duplicate_dashboard(session, dashboard_id)
    if not detail:
        raise HTTPException(404, "Dashboard not found")
    return detail


@router.get("/{dashboard_id}/export")
async def export_dashboard(
    dashboard_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query("pdf", pattern="^(pdf|html|png)$"),
):
    detail = await DashboardService.get_dashboard(session, dashboard_id)
    if not detail:
        raise HTTPException(404, "Dashboard not found")
    if format == "html":
        return HTMLResponse(DashboardService.export_html(detail))
    if format == "pdf":
        data = DashboardService.export_pdf(detail)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{detail.name}.pdf"'},
        )
    return HTMLResponse(
        DashboardService.export_html(detail),
        headers={"Content-Disposition": f'attachment; filename="{detail.name}.html"'},
    )
