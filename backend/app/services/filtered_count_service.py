"""Row counts with dashboard filters applied."""

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import FilterCondition, FilteredCountResponse
from app.services.polars_utils import apply_filters, load_lazy


class FilteredCountService:
    @staticmethod
    def count(
        dataset_id: str,
        filters: list[FilterCondition],
        extra_filters: list[FilterCondition] | None = None,
    ) -> FilteredCountResponse:
        pq = parquet_path(dataset_id)
        if not pq.exists():
            raise ValueError("Dataset not found")
        merged = list(filters) + list(extra_filters or [])
        lf = apply_filters(load_lazy(pq), merged, None)
        total = lf.select(pl.len()).collect().item()
        return FilteredCountResponse(dataset_id=dataset_id, total_rows=int(total))
