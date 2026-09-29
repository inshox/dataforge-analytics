"""Export filtered datasets."""

import io
from pathlib import Path

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import FilterCondition, SortSpec
from app.services.polars_utils import apply_filters, apply_sort, load_lazy


class ExportService:
    @staticmethod
    def export_csv(
        dataset_id: str,
        filters: list[FilterCondition],
        sort: list[SortSpec],
        global_search: str | None,
    ) -> bytes:
        lf = load_lazy(parquet_path(dataset_id))
        lf = apply_filters(lf, filters, global_search)
        lf = apply_sort(lf, sort)
        df = lf.collect()

        buf = io.BytesIO()
        df.write_csv(buf)
        return buf.getvalue()
