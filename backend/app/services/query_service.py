"""Paginated queries with filters and sort."""

import math

import polars as pl

from app.core.config import get_settings
from app.core.storage import parquet_path
from app.models.schemas import ColumnInfo, FilterCondition, RowsResponse, SortSpec
from app.services.polars_utils import (
    apply_filters,
    apply_sort,
    columns_from_json,
    df_to_records,
    load_lazy,
)


class QueryService:
    @staticmethod
    def get_rows(
        dataset_id: str,
        columns_meta: list[ColumnInfo],
        page: int,
        page_size: int,
        filters: list[FilterCondition],
        sort: list[SortSpec],
        global_search: str | None,
    ) -> RowsResponse:
        settings = get_settings()
        page_size = min(page_size, settings.max_page_size)
        pq = parquet_path(dataset_id)
        if not pq.exists():
            return RowsResponse(
                rows=[],
                page=page,
                page_size=page_size,
                total_rows=0,
                total_pages=0,
                columns=columns_meta,
            )

        lf = load_lazy(pq)
        lf = apply_filters(lf, filters, global_search)
        lf = apply_sort(lf, sort)

        total_rows = lf.select(pl.len()).collect().item()
        total_pages = max(1, math.ceil(total_rows / page_size)) if page_size else 1
        offset = (page - 1) * page_size

        df = lf.slice(offset, page_size).collect()
        return RowsResponse(
            rows=df_to_records(df),
            page=page,
            page_size=page_size,
            total_rows=total_rows,
            total_pages=total_pages,
            columns=columns_meta,
        )
