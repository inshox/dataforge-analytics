"""Automatic business insights — local heuristics only."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import InsightItem, InsightsResponse
from app.services.polars_utils import load_frame
from app.services.profiling_service import ProfilingService

NUMERIC = (
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


class InsightsService:
    @staticmethod
    def generate(dataset_id: str) -> InsightsResponse:
        profile = ProfilingService.compute_profile(dataset_id)
        df = load_frame(parquet_path(dataset_id))
        insights: list[InsightItem] = []

        if profile.duplicate_rows > 0:
            pct = 100 * profile.duplicate_rows / max(profile.row_count, 1)
            insights.append(
                InsightItem(
                    id=str(uuid.uuid4()),
                    category="quality",
                    severity="medium" if pct > 5 else "low",
                    message=f"{profile.duplicate_rows:,} duplicate rows ({pct:.1f}% of dataset).",
                    metric="duplicate_rows",
                    value=float(profile.duplicate_rows),
                )
            )

        for col in profile.columns:
            if col.null_percent > 25:
                insights.append(
                    InsightItem(
                        id=str(uuid.uuid4()),
                        category="quality",
                        severity="high" if col.null_percent > 50 else "medium",
                        message=f"Column '{col.column}' has {col.null_percent}% missing values.",
                        metric="null_percent",
                        value=col.null_percent,
                    )
                )
            if col.outlier_count > 0:
                insights.append(
                    InsightItem(
                        id=str(uuid.uuid4()),
                        category="anomaly",
                        severity="medium",
                        message=f"Column '{col.column}' has {col.outlier_count} potential outliers (IQR).",
                        metric="outliers",
                        value=float(col.outlier_count),
                    )
                )

        for col in profile.columns:
            if col.inferred_type == "categorical" and col.top_values:
                top = col.top_values[0]
                share = 100 * top.count / max(profile.row_count, 1)
                if share > 30:
                    insights.append(
                        InsightItem(
                            id=str(uuid.uuid4()),
                            category="distribution",
                            severity="low",
                            message=f"'{top.value}' is the top value in '{col.column}' ({share:.0f}% of rows).",
                            metric="top_share",
                            value=share,
                        )
                    )

        numeric_cols = [c.column for c in profile.columns if c.inferred_type == "numeric"]
        date_cols = [
            c.column
            for c in profile.columns
            if c.inferred_type == "datetime" or "date" in c.column.lower()
        ]

        value_col = _pick_metric_col(numeric_cols)
        date_col = date_cols[0] if date_cols else None

        if date_col and value_col:
            trend = _month_over_month(df, date_col, value_col)
            if trend is not None:
                pct, direction = trend
                insights.append(
                    InsightItem(
                        id=str(uuid.uuid4()),
                        category="trend",
                        severity="low",
                        message=f"{value_col} {direction} {abs(pct):.1f}% month-over-month (approx.).",
                        metric="mom_change_pct",
                        value=pct,
                    )
                )

        if numeric_cols:
            best_corr = _strongest_correlation(profile)
            if best_corr:
                a, b, r = best_corr
                insights.append(
                    InsightItem(
                        id=str(uuid.uuid4()),
                        category="correlation",
                        severity="low",
                        message=f"Strong correlation between '{a}' and '{b}' (r={r:.2f}).",
                        metric="correlation",
                        value=r,
                    )
                )

        if not insights:
            insights.append(
                InsightItem(
                    id=str(uuid.uuid4()),
                    category="summary",
                    severity="low",
                    message=f"Dataset has {profile.row_count:,} rows across {profile.column_count} columns — no major issues detected.",
                )
            )

        return InsightsResponse(
            dataset_id=dataset_id,
            insights=insights,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


def _pick_metric_col(cols: list[str]) -> str | None:
    for kw in ("revenue", "sales", "amount", "total", "price", "value"):
        for c in cols:
            if kw in c.lower():
                return c
    return cols[0] if cols else None


def _month_over_month(df: pl.DataFrame, date_col: str, value_col: str) -> tuple[float, str] | None:
    try:
        work = df.with_columns(pl.col(date_col).cast(pl.Utf8).alias("_d"))
        work = work.with_columns(pl.col("_d").str.slice(0, 7).alias("_month"))
        monthly = work.group_by("_month").agg(pl.col(value_col).cast(pl.Float64).sum().alias("v")).sort("_month")
        if monthly.height < 2:
            return None
        last = float(monthly["v"][-1])
        prev = float(monthly["v"][-2])
        if prev == 0:
            return None
        pct = 100 * (last - prev) / prev
        direction = "increased" if pct >= 0 else "declined"
        return pct, direction
    except Exception:
        return None


def _strongest_correlation(profile) -> tuple[str, str, float] | None:
    if not profile.correlations:
        return None
    best = max(profile.correlations, key=lambda c: abs(c.correlation))
    if abs(best.correlation) < 0.5:
        return None
    return best.column_a, best.column_b, best.correlation
