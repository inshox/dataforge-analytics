"""Seed a ready-to-use demo dataset on first startup."""

from pathlib import Path

import polars as pl
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.storage import parquet_path
from app.models.dataset import DatasetRecord
from app.models.enterprise import DashboardRecord, DashboardWidgetRecord
from app.services.polars_utils import columns_to_json, detect_csv_separator, infer_columns

DEMO_DATASET_ID = "00000000-0000-4000-8000-000000000001"
DEMO_DASHBOARD_ID = "00000000-0000-4000-8000-000000000002"
DEMO_NAME = "Demo — Sales Sample"
DEMO_TAGS = "demo,sample"
DEMO_CSV = Path(__file__).resolve().parent.parent / "data" / "demo_sales.csv"


class DemoService:
    @staticmethod
    async def seed_if_empty(session: AsyncSession) -> DatasetRecord | None:
        """Import bundled CSV when no ready datasets exist."""
        settings = get_settings()
        if not settings.seed_demo_on_startup:
            return None

        ready_count = await session.scalar(
            select(func.count()).select_from(DatasetRecord).where(DatasetRecord.status == "ready")
        )
        if ready_count and ready_count > 0:
            return None

        existing = await session.get(DatasetRecord, DEMO_DATASET_ID)
        if existing and existing.status == "ready":
            return existing

        if not DEMO_CSV.is_file():
            return None

        content = DEMO_CSV.read_bytes()
        separator = detect_csv_separator(content[:8192])
        out = parquet_path(DEMO_DATASET_ID)

        lf = pl.scan_csv(DEMO_CSV, separator=separator, infer_schema_length=10_000, ignore_errors=True)
        lf.sink_parquet(str(out))
        full = pl.read_parquet(str(out))
        columns = infer_columns(full)

        if existing:
            existing.name = DEMO_NAME
            existing.description = "Przykładowe dane sprzedaży — gotowe do eksploracji."
            existing.tags = DEMO_TAGS
            existing.source_filename = DEMO_CSV.name
            existing.source_format = "csv"
            existing.file_size_bytes = len(content)
            existing.row_count = full.height
            existing.column_count = len(full.columns)
            existing.columns_json = columns_to_json(columns)
            existing.status = "ready"
            existing.import_progress = 100
            record = existing
        else:
            record = DatasetRecord(
                id=DEMO_DATASET_ID,
                name=DEMO_NAME,
                description="Przykładowe dane sprzedaży — gotowe do eksploracji.",
                tags=DEMO_TAGS,
                source_filename=DEMO_CSV.name,
                source_format="csv",
                file_size_bytes=len(content),
                row_count=full.height,
                column_count=len(full.columns),
                columns_json=columns_to_json(columns),
                status="ready",
                import_progress=100,
            )
            session.add(record)

        await session.commit()
        await session.refresh(record)
        await DemoService.seed_demo_dashboard(session, record.id)
        return record

    @staticmethod
    async def seed_demo_dashboard(session: AsyncSession, dataset_id: str) -> None:
        from app.services.demo_dashboards_v13 import DemoDashboardsV13

        await DemoDashboardsV13.seed(session, dataset_id)

    @staticmethod
    async def reset_demo(session: AsyncSession) -> DatasetRecord | None:
        """Remove demo dataset files and re-import bundled CSV."""
        import shutil

        settings = get_settings()
        existing = await session.get(DatasetRecord, DEMO_DATASET_ID)
        if existing:
            await session.delete(existing)
            await session.commit()

        pq = parquet_path(DEMO_DATASET_ID)
        if pq.parent.exists():
            shutil.rmtree(pq.parent, ignore_errors=True)

        uploads = list((settings.data_dir.resolve() / "uploads").glob(f"{DEMO_DATASET_ID}_*"))
        for u in uploads:
            u.unlink(missing_ok=True)

        return await DemoService._import_demo(session)

    @staticmethod
    async def _import_demo(session: AsyncSession) -> DatasetRecord | None:
        if not DEMO_CSV.is_file():
            return None
        content = DEMO_CSV.read_bytes()
        separator = detect_csv_separator(content[:8192])
        out = parquet_path(DEMO_DATASET_ID)
        lf = pl.scan_csv(DEMO_CSV, separator=separator, infer_schema_length=10_000, ignore_errors=True)
        lf.sink_parquet(str(out))
        full = pl.read_parquet(str(out))
        columns = infer_columns(full)
        record = DatasetRecord(
            id=DEMO_DATASET_ID,
            name=DEMO_NAME,
            description="Przykładowe dane sprzedaży — gotowe do eksploracji.",
            tags=DEMO_TAGS,
            source_filename=DEMO_CSV.name,
            source_format="csv",
            file_size_bytes=len(content),
            row_count=full.height,
            column_count=len(full.columns),
            columns_json=columns_to_json(columns),
            status="ready",
            import_progress=100,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record
