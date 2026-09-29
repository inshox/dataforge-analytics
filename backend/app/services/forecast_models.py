"""Forecasting 2.0 — Holt-Winters, ARIMA, optional Prophet."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import polars as pl

from app.models.schemas import ForecastPoint


def _parse_base(last_date: str) -> datetime:
    try:
        return datetime.fromisoformat(last_date[:10])
    except ValueError:
        return datetime.now(timezone.utc)


def _z_interval(confidence: float, std: float) -> float:
    if confidence >= 0.99:
        return 2.576 * std
    if confidence >= 0.95:
        return 1.96 * std
    return 1.645 * std


def holt_winters_forecast(
    daily: pl.DataFrame,
    horizon: int,
    seasonal_periods: int | None = None,
    confidence: float = 0.95,
) -> tuple[list[ForecastPoint], bool]:
    ys = [float(v) for v in daily["v"].to_list()]
    dates = [str(d) for d in daily["d"].to_list()]
    n = len(ys)
    period = seasonal_periods or (7 if n >= 14 else None)
    seasonality = False

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        if period and n >= period * 2:
            seasonality = True
            model = ExponentialSmoothing(
                ys,
                trend="add",
                seasonal="add",
                seasonal_periods=period,
            ).fit(optimized=True)
        else:
            model = ExponentialSmoothing(ys, trend="add").fit(optimized=True)
        residuals = ys - model.fittedvalues
        std = (sum(r**2 for r in residuals) / max(n - 1, 1)) ** 0.5
        z = _z_interval(confidence, std)
        points: list[ForecastPoint] = []
        for d, v in zip(dates, ys):
            points.append(ForecastPoint(date=d, value=v, is_forecast=False))
        base = _parse_base(dates[-1])
        for h in range(1, horizon + 1):
            pred = float(model.forecast(h)[-1])
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
        return points, seasonality
    except Exception:
        return _simple_exp(daily, horizon, confidence), False


def arima_forecast(
    daily: pl.DataFrame,
    horizon: int,
    confidence: float = 0.95,
) -> tuple[list[ForecastPoint], bool]:
    ys = [float(v) for v in daily["v"].to_list()]
    dates = [str(d) for d in daily["d"].to_list()]
    try:
        from statsmodels.tsa.arima.model import ARIMA

        model = ARIMA(ys, order=(1, 1, 1)).fit()
        forecast = model.forecast(steps=horizon)
        conf = model.get_forecast(steps=horizon).conf_int(alpha=1 - confidence)
        points: list[ForecastPoint] = []
        for d, v in zip(dates, ys):
            points.append(ForecastPoint(date=d, value=v, is_forecast=False))
        base = _parse_base(dates[-1])
        for h in range(horizon):
            pred = float(forecast.iloc[h])
            lo = float(conf.iloc[h, 0])
            hi = float(conf.iloc[h, 1])
            dt = (base + timedelta(days=h + 1)).strftime("%Y-%m-%d")
            points.append(
                ForecastPoint(
                    date=dt,
                    value=round(pred, 4),
                    lower=round(lo, 4),
                    upper=round(hi, 4),
                    is_forecast=True,
                )
            )
        return points, False
    except Exception:
        return _simple_exp(daily, horizon, confidence), False


def prophet_forecast(
    daily: pl.DataFrame,
    horizon: int,
    confidence: float = 0.95,
) -> tuple[list[ForecastPoint], bool]:
    try:
        import pandas as pd
        from prophet import Prophet
    except ImportError as exc:
        raise ValueError(
            "Prophet is optional. Install with: pip install prophet"
        ) from exc

    pdf = daily.select(["d", "v"]).to_pandas()
    pdf.columns = ["ds", "y"]
    pdf["ds"] = pd.to_datetime(pdf["ds"])
    m = Prophet(interval_width=confidence)
    m.fit(pdf)
    future = m.make_future_dataframe(periods=horizon)
    fc = m.predict(future)
    points: list[ForecastPoint] = []
    hist = fc.iloc[: len(pdf)]
    for _, row in hist.iterrows():
        points.append(
            ForecastPoint(
                date=row["ds"].strftime("%Y-%m-%d"),
                value=round(float(row["yhat"]), 4),
                is_forecast=False,
            )
        )
    tail = fc.iloc[len(pdf) :]
    for _, row in tail.iterrows():
        points.append(
            ForecastPoint(
                date=row["ds"].strftime("%Y-%m-%d"),
                value=round(float(row["yhat"]), 4),
                lower=round(float(row["yhat_lower"]), 4),
                upper=round(float(row["yhat_upper"]), 4),
                is_forecast=True,
            )
        )
    return points, True


def _simple_exp(daily: pl.DataFrame, horizon: int, confidence: float) -> list[ForecastPoint]:
    alpha = 0.3
    ys = daily["v"].to_list()
    level = float(ys[0])
    for y in ys[1:]:
        level = alpha * float(y) + (1 - alpha) * level
    points: list[ForecastPoint] = []
    for row in daily.iter_rows(named=True):
        points.append(ForecastPoint(date=str(row["d"]), value=float(row["v"]), is_forecast=False))
    base = _parse_base(str(daily["d"][-1]))
    z = level * 0.1 * (2 if confidence >= 0.95 else 1.5)
    for h in range(1, horizon + 1):
        dt = (base + timedelta(days=h)).strftime("%Y-%m-%d")
        points.append(
            ForecastPoint(
                date=dt,
                value=round(level, 4),
                lower=round(level - z, 4),
                upper=round(level + z, 4),
                is_forecast=True,
            )
        )
    return points
