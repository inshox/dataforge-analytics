"""Extended data profiling — quality, outliers, top values, correlations."""

from __future__ import annotations

import math

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import (
    ColumnCorrelation,
    ColumnProfile,
    DatasetProfileResponse,
    TopValue,
)
from app.services.polars_utils import load_frame

NUMERIC_DTYPES = (
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
)


def _infer_type(dtype: pl.DataType, unique_ratio: float) -> str:
    if dtype in NUMERIC_DTYPES:
        return "numeric"
    if dtype == pl.Boolean:
        return "boolean"
    if dtype in (pl.Date, pl.Datetime, pl.Time):
        return "datetime"
    if unique_ratio < 0.05 and dtype == pl.Utf8:
        return "categorical"
    return "text"


def _outlier_count(series: pl.Series) -> int:
    if series.dtype not in NUMERIC_DTYPES:
        return 0
    numeric = series.drop_nulls().cast(pl.Float64)
    if numeric.len() < 4:
        return 0
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        return 0
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return int(((numeric < low) | (numeric > high)).sum())


class ProfilingService:
    @staticmethod
    def compute_profile(dataset_id: str) -> DatasetProfileResponse:
        df = load_frame(parquet_path(dataset_id))
        duplicate_rows = df.height - df.unique().height
        n_rows = df.height

        numeric_cols = [c for c in df.columns if df[c].dtype in NUMERIC_DTYPES]
        correlations: list[ColumnCorrelation] = []

        if len(numeric_cols) >= 2:
            for i, col_a in enumerate(numeric_cols):
                for j, col_b in enumerate(numeric_cols):
                    if j <= i:
                        continue
                    try:
                        val = df.select(pl.corr(col_a, col_b)).item()
                    except Exception:
                        continue
                    if val is not None and not (isinstance(val, float) and math.isnan(val)):
                        correlations.append(
                            ColumnCorrelation(
                                column_a=col_a,
                                column_b=col_b,
                                correlation=round(float(val), 4),
                            )
                        )

        columns: list[ColumnProfile] = []
        for col in df.columns:
            series = df[col]
            dtype = str(series.dtype)
            null_count = int(series.null_count())
            count = n_rows - null_count
            unique_count = int(series.n_unique())
            unique_ratio = unique_count / n_rows if n_rows else 0.0

            mean = median = min_v = max_v = std = None
            if series.dtype in NUMERIC_DTYPES:
                numeric = series.drop_nulls()
                if numeric.len() > 0:
                    mean = float(numeric.mean())
                    median = float(numeric.median())
                    min_v = float(numeric.min())
                    max_v = float(numeric.max())
                    std = float(numeric.std()) if numeric.len() > 1 else 0.0

            top_values: list[TopValue] = []
            try:
                vc = (
                    series.drop_nulls()
                    .cast(pl.Utf8)
                    .value_counts()
                    .sort("count", descending=True)
                    .head(5)
                )
                for row in vc.iter_rows():
                    top_values.append(TopValue(value=str(row[0]), count=int(row[1])))
            except Exception:
                pass

            columns.append(
                ColumnProfile(
                    column=col,
                    dtype=dtype,
                    inferred_type=_infer_type(series.dtype, unique_ratio),
                    count=count,
                    null_count=null_count,
                    null_percent=round(100 * null_count / n_rows, 2) if n_rows else 0.0,
                    unique_count=unique_count,
                    mean=mean,
                    median=median,
                    min=min_v,
                    max=max_v,
                    std=std,
                    outlier_count=_outlier_count(series),
                    top_values=top_values,
                )
            )

        insights = _build_insights(columns, duplicate_rows, n_rows)

        return DatasetProfileResponse(
            dataset_id=dataset_id,
            row_count=n_rows,
            column_count=len(df.columns),
            duplicate_rows=duplicate_rows,
            columns=columns,
            correlations=correlations[:30],
            insights=insights,
        )


def _build_insights(columns: list[ColumnProfile], duplicate_rows: int, n_rows: int) -> list[str]:
    insights: list[str] = []
    if duplicate_rows > 0:
        insights.append(f"{duplicate_rows} duplicate rows ({100 * duplicate_rows / max(n_rows, 1):.1f}%)")
    high_null = [c for c in columns if c.null_percent > 20]
    if high_null:
        insights.append(
            f"{len(high_null)} column(s) with >20% missing: {', '.join(c.column for c in high_null[:5])}"
        )
    outliers = [c for c in columns if c.outlier_count > 0]
    if outliers:
        total = sum(c.outlier_count for c in outliers)
        insights.append(f"Potential outliers detected in {len(outliers)} column(s) ({total} points)")
    cats = [c for c in columns if c.inferred_type == "categorical"]
    if cats:
        insights.append(f"{len(cats)} categorical column(s) suitable for grouping charts")
    return insights
