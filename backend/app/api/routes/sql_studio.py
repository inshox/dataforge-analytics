"""Global SQL Studio API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    SavedQueryCreate,
    SavedQueryResponse,
    QueryHistoryItem,
    SqlExecuteRequest,
    SqlExecuteResponse,
)
from app.services.dataset_service import DatasetService
from app.services.sql_studio_service import SqlStudioService

router = APIRouter(prefix="/sql-studio", tags=["sql-studio"])


@router.get("/saved", response_model=list[SavedQueryResponse])
async def list_saved(session: Annotated[AsyncSession, Depends(get_db)]):
    return await SqlStudioService.list_saved(session)


@router.post("/saved", response_model=SavedQueryResponse)
async def save_query(body: SavedQueryCreate, session: Annotated[AsyncSession, Depends(get_db)]):
    return await SqlStudioService.save_query(session, body)


@router.delete("/saved/{query_id}")
async def delete_saved(query_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    if not await SqlStudioService.delete_saved(session, query_id):
        raise HTTPException(404, "Query not found")
    return {"ok": True}


@router.get("/history", response_model=list[QueryHistoryItem])
async def query_history(session: Annotated[AsyncSession, Depends(get_db)], limit: int = 50):
    return await SqlStudioService.list_history(session, limit)


@router.post("/execute", response_model=SqlExecuteResponse)
async def execute_sql(body: SqlExecuteRequest, session: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await SqlStudioService.execute(
            session, body.dataset_id, body.query, body.page, body.page_size
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@router.get("/schema/{dataset_id}")
async def dataset_schema(dataset_id: str, session: Annotated[AsyncSession, Depends(get_db)]):
    record = await DatasetService.get_dataset(session, dataset_id)
    if not record:
        raise HTTPException(404, "Dataset not found")
    return SqlStudioService.schema_for_dataset(dataset_id, record.columns_json)
