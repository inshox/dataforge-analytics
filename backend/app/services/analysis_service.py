"""Column statistics and data quality checks."""

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import ColumnStats, DatasetStatsResponse
from app.services.polars_utils import load_frame


class AnalysisService:
    @staticmethod
    def compute_stats(dataset_id: str) -> DatasetStatsResponse:
        pq = parquet_path(dataset_id)
        df = load_frame(pq)
        duplicate_rows = df.height - df.unique().height

        stats: list[ColumnStats] = []
        for col in df.columns:
            series = df[col]
            dtype = str(series.dtype)
            null_count = int(series.null_count())
            count = int(df.height - null_count)
            unique_count = int(series.n_unique())

            mean = median = min_v = max_v = std = None
            if series.dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64):
                numeric = series.drop_nulls()
                if numeric.len() > 0:
                    mean = float(numeric.mean())
                    median = float(numeric.median())
                    min_v = float(numeric.min())
                    max_v = float(numeric.max())
                    std = float(numeric.std()) if numeric.len() > 1 else 0.0

            stats.append(
                ColumnStats(
                    column=col,
                    dtype=dtype,
                    count=count,
                    null_count=null_count,
                    unique_count=unique_count,
                    mean=mean,
                    median=median,
                    min=min_v,
                    max=max_v,
                    std=std,
                )
            )

        return DatasetStatsResponse(
            dataset_id=dataset_id,
            row_count=df.height,
            column_count=len(df.columns),
            duplicate_rows=duplicate_rows,
            columns=stats,
        )
