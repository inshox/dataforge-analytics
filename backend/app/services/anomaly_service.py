"""Anomaly detection — IQR, z-score, rolling deviation."""

from __future__ import annotations

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import AnomaliesResponse, AnomalyItem, FilterCondition
from app.services.polars_utils import apply_filters, load_lazy

NUMERIC = (
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.Float32,
    pl.Float64,
)


class AnomalyService:
    @staticmethod
    def detect(
        dataset_id: str,
        methods: list[str] | None = None,
        extra_filters: list[FilterCondition] | None = None,
    ) -> AnomaliesResponse:
        methods = methods or ["iqr", "zscore"]
        lf = load_lazy(parquet_path(dataset_id))
        if extra_filters:
            lf = apply_filters(lf, extra_filters, None)
        df = lf.collect()
        anomalies: list[AnomalyItem] = []

        for col in df.columns:
            series = df[col]
            if series.dtype not in NUMERIC:
                continue

            numeric = series.drop_nulls().cast(pl.Float64)
            if numeric.len() < 10:
                continue

            if "iqr" in methods:
                anomalies.extend(_iqr_anomalies(df, col, numeric))
            if "zscore" in methods:
                anomalies.extend(_zscore_anomalies(df, col, numeric))
            if "rolling" in methods:
                anomalies.extend(_rolling_anomalies(numeric, col))

        severity_order = {"high": 0, "medium": 1, "low": 2}
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 3))
        anomalies = anomalies[:100]

        summary = (
            f"Found {len(anomalies)} anomalies across numeric columns."
            if anomalies
            else "No significant anomalies detected."
        )
        return AnomaliesResponse(dataset_id=dataset_id, anomalies=anomalies, summary=summary)


def _iqr_anomalies(df: pl.DataFrame, col: str, numeric: pl.Series) -> list[AnomalyItem]:
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        return []
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    items: list[AnomalyItem] = []
    for idx, val in enumerate(df[col].to_list()):
        if val is None:
            continue
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        if v < low or v > high:
            severity = "high" if v < low - iqr or v > high + iqr else "medium"
            items.append(
                AnomalyItem(
                    column=col,
                    row_index=idx,
                    value=v,
                    severity=severity,
                    method="iqr",
                    explanation=f"Value {v:.2f} outside IQR bounds [{low:.2f}, {high:.2f}].",
                )
            )
            if len(items) >= 20:
                break
    return items


def _zscore_anomalies(df: pl.DataFrame, col: str, numeric: pl.Series) -> list[AnomalyItem]:
    mean = float(numeric.mean())
    std = float(numeric.std()) or 1.0
    items: list[AnomalyItem] = []
    for idx, val in enumerate(df[col].to_list()):
        if val is None:
            continue
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        z = abs((v - mean) / std)
        if z >= 3:
            items.append(
                AnomalyItem(
                    column=col,
                    row_index=idx,
                    value=v,
                    severity="high" if z >= 4 else "medium",
                    method="zscore",
                    explanation=f"Z-score {z:.2f} (mean={mean:.2f}, std={std:.2f}).",
                )
            )
            if len(items) >= 15:
                break
    return items


def _rolling_anomalies(numeric: pl.Series, col: str) -> list[AnomalyItem]:
    if numeric.len() < 20:
        return []
    window = 7
    rolled = numeric.rolling_mean(window_size=window)
    std = numeric.rolling_std(window_size=window)
    items: list[AnomalyItem] = []
    for i in range(window, numeric.len()):
        v = float(numeric[i])
        m = float(rolled[i]) if rolled[i] is not None else v
        s = float(std[i]) if std[i] is not None else 0.0
        if s > 0 and abs(v - m) > 2.5 * s:
            items.append(
                AnomalyItem(
                    column=col,
                    row_index=i,
                    value=v,
                    severity="medium",
                    method="rolling",
                    explanation=f"Deviation from {window}-period rolling mean ({m:.2f}).",
                )
            )
            if len(items) >= 10:
                break
    return items
