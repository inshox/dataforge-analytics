"""SQL Studio — saved queries, history, schema."""

from __future__ import annotations

import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import QueryHistoryRecord, SavedQueryRecord
from app.models.schemas import (
    QueryHistoryItem,
    SavedQueryCreate,
    SavedQueryResponse,
    SqlExecuteResponse,
)
from app.services.dataset_service import DatasetService
from app.services.sql_service import SqlService


class SqlStudioService:
    @staticmethod
    async def list_saved(session: AsyncSession) -> list[SavedQueryResponse]:
        result = await session.execute(
            select(SavedQueryRecord).order_by(SavedQueryRecord.updated_at.desc())
        )
        return [SqlStudioService._saved_to_response(r) for r in result.scalars().all()]

    @staticmethod
    async def save_query(session: AsyncSession, body: SavedQueryCreate) -> SavedQueryResponse:
        rec = SavedQueryRecord(
            id=str(uuid.uuid4()),
            name=body.name,
            dataset_id=body.dataset_id,
            sql_text=body.sql_text,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return SqlStudioService._saved_to_response(rec)

    @staticmethod
    async def delete_saved(session: AsyncSession, query_id: str) -> bool:
        rec = await session.get(SavedQueryRecord, query_id)
        if not rec:
            return False
        await session.delete(rec)
        await session.commit()
        return True

    @staticmethod
    async def list_history(session: AsyncSession, limit: int = 50) -> list[QueryHistoryItem]:
        result = await session.execute(
            select(QueryHistoryRecord).order_by(QueryHistoryRecord.created_at.desc()).limit(limit)
        )
        return [SqlStudioService._history_to_response(r) for r in result.scalars().all()]

    @staticmethod
    async def execute(
        session: AsyncSession,
        dataset_id: str,
        query: str,
        page: int,
        page_size: int,
    ) -> SqlExecuteResponse:
        record = await DatasetService.get_dataset(session, dataset_id)
        if not record:
            raise ValueError("Dataset not found")
        if record.status != "ready":
            raise ValueError("Dataset not ready")

        start = time.perf_counter()
        success = True
        error_message = None
        try:
            result = SqlService.execute(dataset_id, query, page, page_size)
            rows_returned = result.total_rows
        except Exception as exc:
            success = False
            error_message = str(exc)
            runtime_ms = (time.perf_counter() - start) * 1000
            hist = QueryHistoryRecord(
                dataset_id=dataset_id,
                sql_text=query,
                runtime_ms=runtime_ms,
                rows_returned=0,
                success=0,
                error_message=error_message,
            )
            session.add(hist)
            await session.commit()
            raise

        runtime_ms = (time.perf_counter() - start) * 1000
        hist = QueryHistoryRecord(
            dataset_id=dataset_id,
            sql_text=query,
            runtime_ms=runtime_ms,
            rows_returned=rows_returned,
            success=1,
        )
        session.add(hist)
        await session.commit()

        return SqlExecuteResponse(
            columns=result.columns,
            rows=result.rows,
            page=result.page,
            page_size=result.page_size,
            total_rows=result.total_rows,
            runtime_ms=round(runtime_ms, 2),
            success=True,
        )

    @staticmethod
    def schema_for_dataset(dataset_id: str, columns_json: str | None) -> dict:
        from app.services.polars_utils import columns_from_json

        cols = columns_from_json(columns_json)
        return {
            "dataset_id": dataset_id,
            "view_name": "dataset",
            "columns": [{"name": c.name, "dtype": c.dtype} for c in cols],
        }

    @staticmethod
    def _saved_to_response(r: SavedQueryRecord) -> SavedQueryResponse:
        return SavedQueryResponse(
            id=r.id,
            name=r.name,
            dataset_id=r.dataset_id,
            sql_text=r.sql_text,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )

    @staticmethod
    def _history_to_response(r: QueryHistoryRecord) -> QueryHistoryItem:
        return QueryHistoryItem(
            id=r.id,
            dataset_id=r.dataset_id,
            sql_text=r.sql_text,
            runtime_ms=r.runtime_ms,
            rows_returned=r.rows_returned,
            success=bool(r.success),
            error_message=r.error_message,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
