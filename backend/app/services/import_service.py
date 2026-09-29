"""Dataset import — CSV, XLSX, Parquet, JSON."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import polars as pl
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.storage import parquet_path, upload_path
from app.models.dataset import DatasetRecord
from app.models.schemas import ImportPreviewResponse
from app.services.file_validation import detect_format, validate_upload
from app.services.import_registry import clear_cancelled, is_cancelled, mark_cancelled
from app.services.polars_utils import columns_to_json, detect_csv_separator, infer_columns


class ImportService:
    @staticmethod
    async def preview_file(
        session: AsyncSession,
        file_content: bytes,
        filename: str,
        name: str | None = None,
        separator_override: str | None = None,
    ) -> ImportPreviewResponse:
        validation = validate_upload(file_content, filename, separator_override)
        if not validation.ok:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "; ".join(validation.errors),
                    "code": "validation_failed",
                    "errors": validation.errors,
                },
            )

        settings = get_settings()
        dataset_id = str(uuid.uuid4())
        upload_file = upload_path(f"{dataset_id}_{filename}")
        upload_file.write_bytes(file_content)
        clear_cancelled(dataset_id)

        fmt = validation.format
        df = _read_preview_frame(upload_file, fmt, validation, settings.preview_rows)
        columns = infer_columns(df)
        row_estimate = _estimate_rows(upload_file, fmt)

        record = DatasetRecord(
            id=dataset_id,
            name=name or Path(filename).stem,
            source_filename=filename,
            source_format=fmt,
            file_size_bytes=len(file_content),
            row_count=row_estimate or len(df),
            column_count=len(columns),
            columns_json=columns_to_json(columns),
            status="preview",
            import_progress=0,
        )
        session.add(record)
        await session.commit()

        return ImportPreviewResponse(
            dataset_id=dataset_id,
            preview_rows=df.to_dicts(),
            columns=columns,
            row_count_estimate=row_estimate,
            file_size_bytes=len(file_content),
            detected_separator=validation.separator,
            detected_encoding=validation.encoding,
            detected_format=fmt,
            validation_warnings=validation.warnings,
        )

    @staticmethod
    async def preview_csv(
        session: AsyncSession,
        file_content: bytes,
        filename: str,
        name: str | None = None,
        separator_override: str | None = None,
    ) -> ImportPreviewResponse:
        return await ImportService.preview_file(
            session, file_content, filename, name, separator_override
        )

    @staticmethod
    async def cancel_import(session: AsyncSession, dataset_id: str) -> None:
        mark_cancelled(dataset_id)
        record = await session.get(DatasetRecord, dataset_id)
        if not record:
            return
        if record.status != "preview":
            return
        uploads = list((get_settings().data_dir.resolve() / "uploads").glob(f"{dataset_id}_*"))
        for u in uploads:
            u.unlink(missing_ok=True)
        await session.delete(record)
        await session.commit()
        clear_cancelled(dataset_id)

    @staticmethod
    async def finalize_import(session: AsyncSession, dataset_id: str) -> DatasetRecord:
        if is_cancelled(dataset_id):
            raise ValueError("Import was cancelled")

        settings = get_settings()
        record = await session.get(DatasetRecord, dataset_id)
        if not record:
            raise ValueError("Dataset not found")

        uploads = list((settings.data_dir.resolve() / "uploads").glob(f"{dataset_id}_*"))
        if not uploads:
            raise ValueError("Upload file missing")
        upload_file = uploads[0]
        fmt = record.source_format or detect_format(upload_file.name)

        record.status = "importing"
        record.import_progress = 5
        record.import_stage = "reading"
        await session.commit()

        out = parquet_path(dataset_id)
        try:
            record.import_stage = "validating"
            record.import_progress = 15
            await session.commit()
            lf = _scan_upload(upload_file, fmt)
            if is_cancelled(dataset_id):
                raise ValueError("Import was cancelled")
            record.import_stage = "converting"
            record.import_progress = 45
            await session.commit()
            lf.sink_parquet(str(out))
            record.import_stage = "indexing"
            record.import_progress = 75
            await session.commit()
            record.import_stage = "profiling"
            record.import_progress = 90
            await session.commit()
        except Exception as exc:
            record.status = "error"
            record.import_progress = 0
            record.import_stage = "failed"
            await session.commit()
            raise ValueError(str(exc)) from exc

        meta = pl.scan_parquet(str(out)).select(pl.len()).collect()
        record.row_count = int(meta.item())
        schema = pl.scan_parquet(str(out)).collect_schema()
        record.column_count = len(schema.names())
        sample = pl.scan_parquet(str(out)).head(5000).collect()
        record.columns_json = columns_to_json(infer_columns(sample))
        record.status = "ready"
        record.import_progress = 100
        record.import_stage = "complete"
        await session.commit()
        await session.refresh(record)
        clear_cancelled(dataset_id)
        return record

    @staticmethod
    async def finalize_csv_import(session: AsyncSession, dataset_id: str) -> DatasetRecord:
        return await ImportService.finalize_import(session, dataset_id)


def _read_preview_frame(
    path: Path,
    fmt: str,
    validation,
    n_rows: int,
) -> pl.DataFrame:
    if fmt == "csv":
        sep = validation.separator or ","
        try:
            return pl.read_csv(
                path,
                separator=sep,
                n_rows=n_rows,
                infer_schema_length=1000,
                ignore_errors=True,
            )
        except Exception:
            return pl.read_csv(
                path,
                separator=sep,
                n_rows=n_rows,
                infer_schema_length=1000,
                ignore_errors=True,
                encoding="latin-1",
            )
    if fmt == "xlsx":
        return pl.read_excel(path, n_rows=n_rows)
    if fmt == "parquet":
        return pl.read_parquet(path).head(n_rows)
    if fmt == "json":
        return _read_json_frame(path, n_rows)
    raise ValueError(f"Unsupported format: {fmt}")


def _read_json_frame(path: Path, n_rows: int) -> pl.DataFrame:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    return pl.DataFrame(data).head(n_rows)


def _scan_upload(path: Path, fmt: str) -> pl.LazyFrame:
    if fmt == "csv":
        sep = detect_csv_separator(path.read_bytes()[:8192])
        return pl.scan_csv(path, separator=sep, infer_schema_length=10_000, ignore_errors=True)
    if fmt == "xlsx":
        return pl.read_excel(path).lazy()
    if fmt == "parquet":
        return pl.scan_parquet(path)
    if fmt == "json":
        return _read_json_frame(path, 10_000_000).lazy()
    raise ValueError(f"Unsupported format: {fmt}")


def _estimate_rows(path: Path, fmt: str) -> int | None:
    if fmt == "csv":
        try:
            with path.open("rb") as f:
                return sum(1 for _ in f) - 1
        except OSError:
            return None
    if fmt == "parquet":
        try:
            return pl.scan_parquet(path).select(pl.len()).collect().item()
        except Exception:
            return None
    try:
        return _read_preview_frame(path, fmt, type("V", (), {"separator": ","})(), 1_000_000).height
    except Exception:
        return None
