"""Dataset REST endpoints."""

import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    AggregateRequest,
    AggregateResponse,
    AiAnalystExecuteRequest,
    AiAnalystRequest,
    AiAnalystResponse,
    ChartRequest,
    ChartResponse,
    AnomaliesResponse,
    AnomalyDetectRequest,
    DatasetProfileResponse,
    DatasetStatsResponse,
    ForecastRequest,
    ForecastResponse,
    InsightsResponse,
    DatasetSummary,
    DistinctValuesResponse,
    FilterCondition,
    FilteredCountRequest,
    FilteredCountResponse,
    ImportPreviewResponse,
    RowsResponse,
    SortSpec,
    SqlRequest,
    SqlResponse,
    TableViewResponse,
    TableViewSpec,
)
from app.services.ai_analyst_service import AiAnalystService
from app.services.analysis_service import AnalysisService
from app.services.chart_service import ChartService
from app.services.dataset_service import DatasetService
from app.services.export_service import ExportService
from app.services.aggregate_service import AggregateService
from app.services.distinct_service import DistinctService
from app.services.filtered_count_service import FilteredCountService
from app.services.import_background import finalize_import_background, is_import_running
from app.services.import_service import ImportService
from app.services.anomaly_service import AnomalyService
from app.services.forecast_service import ForecastService
from app.services.insights_service import InsightsService
from app.services.profiling_service import ProfilingService
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.services.sql_service import SqlService

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetSummary])
async def list_datasets(
    session: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = None,
):
    return await DatasetService.list_datasets(session, search)


@router.get("/{dataset_id}", response_model=DatasetSummary)
async def get_dataset(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    return DatasetService.to_summary(record)


@router.post("/import/preview", response_model=ImportPreviewResponse)
async def import_preview(
    session: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    name: str | None = Form(None),
    separator: str | None = Form(None, description="Override delimiter: , ; \\t |"),
):
    content = await file.read()
    if not file.filename:
        raise HTTPException(400, detail={"message": "Filename required", "code": "missing_filename"})
    return await ImportService.preview_file(session, content, file.filename, name, separator)


@router.post("/{dataset_id}/import/cancel")
async def cancel_import(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    await ImportService.cancel_import(session, dataset_id)
    return {"ok": True}


@router.post("/{dataset_id}/import/finalize", response_model=DatasetSummary)
async def finalize_import(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    background: bool = Query(False, description="Run import in background with live progress"),
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if background:
        if record.status == "importing" or is_import_running(dataset_id):
            return DatasetService.to_summary(record)
        record.status = "importing"
        record.import_progress = 5
        await session.commit()
        await session.refresh(record)
        background_tasks.add_task(finalize_import_background, dataset_id)
        return DatasetService.to_summary(record)
    try:
        record = await ImportService.finalize_import(session, dataset_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return DatasetService.to_summary(record)


@router.post("/{dataset_id}/aggregate", response_model=AggregateResponse)
async def aggregate_dataset(
    dataset_id: str,
    body: AggregateRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    try:
        return AggregateService.aggregate(dataset_id, body, extra_filters=body.extra_filters)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/{dataset_id}/columns/{column_name}/distinct", response_model=DistinctValuesResponse)
async def column_distinct(
    dataset_id: str,
    column_name: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(500, ge=1, le=2000),
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    try:
        return DistinctService.distinct_values(dataset_id, column_name, limit)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/{dataset_id}/filtered-count", response_model=FilteredCountResponse)
async def filtered_count(
    dataset_id: str,
    body: FilteredCountRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    try:
        return FilteredCountService.count(dataset_id, body.filters, body.extra_filters)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/{dataset_id}/rows", response_model=RowsResponse)
async def get_rows(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    sort: str | None = Query(None, description="JSON array of {column, descending}"),
    filters: str | None = Query(None, description="JSON array of filter conditions"),
    q: str | None = Query(None, description="Global search"),
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    sort_specs = [SortSpec(**s) for s in json.loads(sort)] if sort else []
    filter_specs = [FilterCondition(**f) for f in json.loads(filters)] if filters else []
    columns = DatasetService.to_summary(record).columns
    return QueryService.get_rows(dataset_id, columns, page, page_size, filter_specs, sort_specs, q)


@router.get("/{dataset_id}/stats", response_model=DatasetStatsResponse)
async def get_stats(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    return AnalysisService.compute_stats(dataset_id)


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
async def get_profile(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    return ProfilingService.compute_profile(dataset_id)


@router.post("/{dataset_id}/insights", response_model=InsightsResponse)
async def generate_insights(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    return InsightsService.generate(dataset_id)


@router.post("/{dataset_id}/forecast", response_model=ForecastResponse)
async def forecast_dataset(
    dataset_id: str,
    body: ForecastRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    try:
        return ForecastService.forecast(dataset_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/{dataset_id}/forecast/export/csv")
async def forecast_export_csv(
    dataset_id: str,
    body: ForecastRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    try:
        result = ForecastService.forecast(dataset_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    lines = ["date,value,lower,upper,is_forecast"]
    for p in result.points:
        lines.append(
            f"{p.date},{p.value},{p.lower or ''},{p.upper or ''},{str(p.is_forecast).lower()}"
        )
    content = "\n".join(lines)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="forecast-{dataset_id}.csv"'},
    )


@router.post("/{dataset_id}/anomalies", response_model=AnomaliesResponse)
async def detect_anomalies(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    body: AnomalyDetectRequest | None = None,
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    req = body or AnomalyDetectRequest()
    return AnomalyService.detect(
        dataset_id, methods=req.methods, extra_filters=req.extra_filters
    )


@router.post("/{dataset_id}/ai/analyze", response_model=AiAnalystResponse)
async def ai_analyze(
    dataset_id: str,
    body: AiAnalystRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    summary = DatasetService.to_summary(record)
    return AiAnalystService.analyze(dataset_id, body.question, summary.columns)


@router.post("/{dataset_id}/ai/execute", response_model=SqlResponse)
async def ai_execute(
    dataset_id: str,
    body: AiAnalystExecuteRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    try:
        return AiAnalystService.execute(dataset_id, body.sql, body.page, body.page_size)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/{dataset_id}/report")
async def generate_report(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query("html", pattern="^(html|pdf)$"),
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    if record.status != "ready":
        raise HTTPException(400, "Dataset not ready")
    if format == "pdf":
        data = ReportService.generate_pdf(dataset_id, record.name)
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{record.name}-report.pdf"'},
        )
    html = ReportService.generate_html(dataset_id, record.name)
    return HTMLResponse(content=html)


@router.post("/{dataset_id}/charts", response_model=ChartResponse)
async def build_chart(dataset_id: str, body: ChartRequest, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    try:
        return ChartService.build_chart(dataset_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.post("/{dataset_id}/sql", response_model=SqlResponse)
async def run_sql(dataset_id: str, body: SqlRequest, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    try:
        return SqlService.execute(dataset_id, body.query, body.page, body.page_size)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/{dataset_id}/export/csv")
async def export_csv(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    filters: str | None = None,
    sort: str | None = None,
    q: str | None = None,
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    sort_specs = [SortSpec(**s) for s in json.loads(sort)] if sort else []
    filter_specs = [FilterCondition(**f) for f in json.loads(filters)] if filters else []
    data = ExportService.export_csv(dataset_id, filter_specs, sort_specs, q)
    filename = f"{record.name}.csv"
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{dataset_id}/views", response_model=list[TableViewResponse])
async def list_views(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    return await DatasetService.list_table_views(session, dataset_id)


@router.post("/{dataset_id}/views", response_model=TableViewResponse)
async def save_view(
    dataset_id: str,
    body: TableViewSpec,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    return await DatasetService.save_table_view(
        session, dataset_id, body.name, body.filters, body.sort, body.hidden_columns
    )


@router.delete("/{dataset_id}/views/{view_id}")
async def delete_view(
    dataset_id: str,
    view_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    ok = await DatasetService.delete_table_view(session, view_id)
    if not ok:
        raise HTTPException(404, "View not found")
    return {"ok": True}


@router.post("/{dataset_id}/filter-presets")
async def save_filter_preset(
    dataset_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    name: str = Form(...),
    filters: str = Form(...),
):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    filter_specs = [FilterCondition(**f) for f in json.loads(filters)]
    preset = await DatasetService.save_filter_preset(session, dataset_id, name, filter_specs)
    return {"id": preset.id, "name": preset.name}
