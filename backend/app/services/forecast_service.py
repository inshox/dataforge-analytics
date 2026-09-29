"""Time-series forecasting — linear, exponential, Holt-Winters, ARIMA, Prophet."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import ForecastPoint, ForecastRequest, ForecastResponse
from app.services.forecast_models import arima_forecast, holt_winters_forecast, prophet_forecast
from app.services.polars_utils import apply_filters, load_lazy


class ForecastService:
    @staticmethod
    def forecast(dataset_id: str, req: ForecastRequest) -> ForecastResponse:
        lf = load_lazy(parquet_path(dataset_id))
        if req.extra_filters:
            lf = apply_filters(lf, req.extra_filters, None)
        df = lf.collect()
        if req.date_column not in df.columns or req.value_column not in df.columns:
            raise ValueError("Date or value column not found")

        work = df.select(
            [
                pl.col(req.date_column).cast(pl.Utf8).alias("d"),
                pl.col(req.value_column).cast(pl.Float64).alias("v"),
            ]
        ).drop_nulls()

        daily = work.group_by("d").agg(pl.col("v").sum().alias("v")).sort("d")
        if daily.height < 3:
            raise ValueError("Need at least 3 time periods for forecasting")

        method = req.method.lower().replace("-", "_")
        horizon = min(max(req.horizon_days, 7), 365)
        confidence = min(max(req.confidence_level, 0.5), 0.99)
        seasonality = False

        if method in ("holt_winters", "holtwinters", "seasonal"):
            points, seasonality = holt_winters_forecast(
                daily, horizon, req.seasonal_periods, confidence
            )
            summary = f"Holt-Winters forecast for {req.value_column} ({horizon} days)."
        elif method == "arima":
            points, seasonality = arima_forecast(daily, horizon, confidence)
            summary = f"ARIMA forecast for {req.value_column} ({horizon} days)."
        elif method == "prophet":
            points, seasonality = prophet_forecast(daily, horizon, confidence)
            summary = f"Prophet forecast for {req.value_column} ({horizon} days)."
        elif method == "exponential":
            points = _exp_smoothing(daily, horizon, confidence)
            summary = f"Exponential smoothing forecast for {req.value_column} over {horizon} days."
        else:
            points = _linear_forecast(daily, horizon, confidence)
            summary = f"Linear trend forecast for {req.value_column} over {horizon} days."

        prediction_table = [
            {
                "date": p.date,
                "value": p.value,
                "lower": p.lower,
                "upper": p.upper,
                "is_forecast": p.is_forecast,
            }
            for p in points
            if p.is_forecast
        ]

        return ForecastResponse(
            dataset_id=dataset_id,
            method=method,
            horizon_days=horizon,
            points=points,
            summary=summary,
            seasonality_detected=seasonality,
            prediction_table=prediction_table,
        )


def _linear_forecast(daily: pl.DataFrame, horizon: int, confidence: float) -> list[ForecastPoint]:
    n = daily.height
    ys = daily["v"].to_list()
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
    den = sum((x - x_mean) ** 2 for x in xs) or 1
    slope = num / den
    intercept = y_mean - slope * x_mean
    residuals = [ys[i] - (intercept + slope * xs[i]) for i in range(n)]
    std = (sum(r**2 for r in residuals) / max(n - 1, 1)) ** 0.5
    z = 1.96 * std if confidence >= 0.95 else 1.645 * std

    points: list[ForecastPoint] = []
    for row in daily.iter_rows(named=True):
        points.append(ForecastPoint(date=str(row["d"]), value=float(row["v"]), is_forecast=False))

    last_date = str(daily["d"][-1])
    try:
        base = datetime.fromisoformat(last_date[:10])
    except ValueError:
        base = datetime.now(timezone.utc)

    for h in range(1, horizon + 1):
        x_future = n + h - 1
        pred = intercept + slope * x_future
        dt = (base + timedelta(days=h)).strftime("%Y-%m-%d")
        points.append(
            ForecastPoint(
                date=dt,
                value=round(pred, 4),
                lower=round(pred - z, 4),
                upper=round(pred + z, 4),
                is_forecast=True,
            )
        )
    return points


def _exp_smoothing(daily: pl.DataFrame, horizon: int, confidence: float) -> list[ForecastPoint]:
    alpha = 0.3
    ys = daily["v"].to_list()
    level = ys[0]
    for y in ys[1:]:
        level = alpha * y + (1 - alpha) * level

    points: list[ForecastPoint] = []
    for row in daily.iter_rows(named=True):
        points.append(ForecastPoint(date=str(row["d"]), value=float(row["v"]), is_forecast=False))

    last_date = str(daily["d"][-1])
    try:
        base = datetime.fromisoformat(last_date[:10])
    except ValueError:
        base = datetime.now(timezone.utc)

    spread = 0.1 if confidence >= 0.95 else 0.15
    pred = level
    for h in range(1, horizon + 1):
        dt = (base + timedelta(days=h)).strftime("%Y-%m-%d")
        points.append(
            ForecastPoint(
                date=dt,
                value=round(pred, 4),
                lower=round(pred * (1 - spread), 4),
                upper=round(pred * (1 + spread), 4),
                is_forecast=True,
            )
        )
    return points
