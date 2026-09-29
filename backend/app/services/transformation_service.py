"""Power Query–style transformation pipelines (Polars)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import polars as pl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import parquet_path
from app.models.schemas import (
    ColumnInfo,
    TransformPipelineCreate,
    TransformPipelineResponse,
    TransformPreviewRequest,
    TransformPreviewResponse,
    TransformStep,
)
from app.models.v12 import TransformationPipelineRecord
from app.services.polars_utils import apply_filters, columns_to_json, infer_columns, load_lazy


class TransformationService:
    @staticmethod
    def preview(dataset_id: str, body: TransformPreviewRequest) -> TransformPreviewResponse:
        lf = load_lazy(parquet_path(dataset_id))
        lf = TransformationService._apply_steps(lf, body.steps)
        df = lf.head(body.limit).collect()
        cols = infer_columns(df)
        total = lf.select(pl.len()).collect().item()
        return TransformPreviewResponse(
            columns=cols,
            rows=df.to_dicts(),
            row_count=int(total),
        )

    @staticmethod
    def _apply_steps(lf: pl.LazyFrame, steps: list[TransformStep]) -> pl.LazyFrame:
        for step in steps:
            op = step.op
            p = step.params
            if op == "rename":
                lf = lf.rename({p["from"]: p["to"]})
            elif op == "cast":
                dtype_map = {
                    "utf8": pl.Utf8,
                    "int": pl.Int64,
                    "float": pl.Float64,
                    "bool": pl.Boolean,
                    "date": pl.Date,
                }
                pl_type = dtype_map.get(str(p.get("dtype", "utf8")).lower(), pl.Utf8)
                lf = lf.with_columns(pl.col(p["column"]).cast(pl_type))
            elif op == "filter_rows":
                from app.models.schemas import FilterCondition

                cond = FilterCondition(**p["filter"])
                lf = apply_filters(lf, [cond], None)
            elif op == "remove_duplicates":
                subset = p.get("columns")
                lf = lf.unique(subset=subset) if subset else lf.unique()
            elif op == "calculated_column":
                lf = lf.with_columns(pl.lit(p.get("value", 0)).alias(p["name"]))
            elif op == "select_columns":
                lf = lf.select(p["columns"])
            elif op == "group_by":
                aggs = [getattr(pl.col(p["value_column"]), p.get("agg", "sum"))().alias(p["alias"])]
                lf = lf.group_by(p["group_column"]).agg(aggs)
        return lf

    @staticmethod
    async def list_pipelines(
        session: AsyncSession, dataset_id: str
    ) -> list[TransformPipelineResponse]:
        q = select(TransformationPipelineRecord).where(
            TransformationPipelineRecord.dataset_id == dataset_id
        )
        rows = (await session.execute(q)).scalars().all()
        return [TransformationService._to_pipeline_response(r) for r in rows]

    @staticmethod
    async def save_pipeline(
        session: AsyncSession, dataset_id: str, body: TransformPipelineCreate
    ) -> TransformPipelineResponse:
        rec = TransformationPipelineRecord(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            name=body.name,
            steps_json=json.dumps([s.model_dump() for s in body.steps]),
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return TransformationService._to_pipeline_response(rec)

    @staticmethod
    async def run_pipeline(
        session: AsyncSession, dataset_id: str, pipeline_id: str
    ) -> dict:
        rec = await session.get(TransformationPipelineRecord, pipeline_id)
        if not rec or rec.dataset_id != dataset_id:
            raise ValueError("Pipeline not found")
        steps = [TransformStep(**s) for s in json.loads(rec.steps_json)]
        lf = TransformationService._apply_steps(load_lazy(parquet_path(dataset_id)), steps)
        out = parquet_path(dataset_id)
        lf.sink_parquet(str(out))
        schema = pl.scan_parquet(str(out)).collect_schema()
        row_count = pl.scan_parquet(str(out)).select(pl.len()).collect().item()
        return {"ok": True, "row_count": int(row_count), "column_count": len(schema.names())}

    @staticmethod
    def _to_pipeline_response(rec: TransformationPipelineRecord) -> TransformPipelineResponse:
        steps = [TransformStep(**s) for s in json.loads(rec.steps_json or "[]")]
        return TransformPipelineResponse(
            id=rec.id,
            dataset_id=rec.dataset_id,
            name=rec.name,
            steps=steps,
            created_at=rec.created_at.isoformat() if rec.created_at else None,
        )
