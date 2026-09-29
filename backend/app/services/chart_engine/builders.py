"""Production chart data builders (Polars + DuckDB-ready aggregates)."""

from __future__ import annotations

import math

import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import (
    ChartDataPoint,
    ChartLink,
    ChartNode,
    ChartRequest,
    ChartResponse,
)
from app.services.polars_utils import apply_filters, load_lazy


def _lf(dataset_id: str, req: ChartRequest) -> pl.LazyFrame:
    merged = list(req.filters) + list(req.extra_filters)
    return apply_filters(load_lazy(parquet_path(dataset_id)), merged, None)


def _agg_expr(column: str, agg: str) -> pl.Expr:
    col = pl.col(column)
    mapping = {
        "sum": col.sum(),
        "mean": col.mean(),
        "avg": col.mean(),
        "count": pl.len(),
        "min": col.min(),
        "max": col.max(),
        "median": col.median(),
    }
    return mapping.get(agg.lower(), pl.len())


def build_bar_line(dataset_id: str, req: ChartRequest) -> ChartResponse:
    lf = _lf(dataset_id, req)
    agg = req.aggregation.lower()
    y_col = req.y_column or req.x_column
    chart_type = req.chart_type.lower()

    if chart_type == "pie" or agg == "count":
        grouped = (
            lf.group_by(req.x_column)
            .agg(pl.len().alias("value"))
            .sort("value", descending=True)
            .limit(req.limit)
            .collect()
        )
    else:
        grouped = (
            lf.group_by(req.x_column)
            .agg(_agg_expr(y_col, agg).alias("value"))
            .sort("value", descending=True)
            .limit(req.limit)
            .collect()
        )

    data = [
        ChartDataPoint(label=str(row[req.x_column]), value=float(row["value"] or 0))
        for row in grouped.iter_rows(named=True)
    ]
    return ChartResponse(chart_type=req.chart_type, data=data, meta={"x": req.x_column, "y": y_col})


def build_scatter(dataset_id: str, req: ChartRequest) -> ChartResponse:
    y_col = req.y_column or req.x_column
    sampled = _lf(dataset_id, req).select([req.x_column, y_col]).limit(req.limit).collect()
    data = [
        ChartDataPoint(
            label=str(row[req.x_column]),
            value=float(row[y_col] or 0),
            series=y_col,
            extra={"x": row[req.x_column], "y": row[y_col]},
        )
        for row in sampled.iter_rows(named=True)
    ]
    return ChartResponse(chart_type="scatter", data=data, meta={"x": req.x_column, "y": y_col})


def build_bubble(dataset_id: str, req: ChartRequest) -> ChartResponse:
    z_col = req.z_column or req.y_column or req.x_column
    y_col = req.y_column or req.x_column
    cols = list({req.x_column, y_col, z_col})
    df = _lf(dataset_id, req).select(cols).limit(req.limit).collect()
    data = []
    for row in df.iter_rows(named=True):
        data.append(
            ChartDataPoint(
                label=str(row[req.x_column]),
                value=float(row[z_col] or 0),
                extra={
                    "x": float(row[req.x_column]) if _is_num(row[req.x_column]) else row[req.x_column],
                    "y": float(row[y_col] or 0),
                    "z": float(row[z_col] or 0),
                },
            )
        )
    return ChartResponse(chart_type="bubble", data=data, meta={"x": req.x_column, "y": y_col, "z": z_col})


def build_sankey(dataset_id: str, req: ChartRequest) -> ChartResponse:
    src = req.source_column or req.config.get("source_column") or req.x_column
    tgt = req.target_column or req.config.get("target_column") or req.y_column
    val_col = req.config.get("value_column") or req.z_column
    if not tgt:
        raise ValueError("Sankey requires target_column")
    agg = _agg_expr(val_col, req.aggregation) if val_col else pl.len()
    grouped = (
        _lf(dataset_id, req)
        .group_by([src, tgt])
        .agg(agg.alias("value"))
        .sort("value", descending=True)
        .limit(req.limit)
        .collect()
    )
    links = [
        ChartLink(source=str(r[src]), target=str(r[tgt]), value=float(r["value"] or 0))
        for r in grouped.iter_rows(named=True)
    ]
    nodes_map: dict[str, ChartNode] = {}
    for link in links:
        for nid, name in ((link.source, link.source), (link.target, link.target)):
            if nid not in nodes_map:
                nodes_map[nid] = ChartNode(id=nid, name=name, value=0)
    for link in links:
        nodes_map[link.source].value = (nodes_map[link.source].value or 0) + link.value
    return ChartResponse(
        chart_type="sankey",
        data=[],
        nodes=list(nodes_map.values()),
        links=links,
        meta={"source": src, "target": tgt},
    )


def build_funnel(dataset_id: str, req: ChartRequest) -> ChartResponse:
    stage_col = req.x_column
    val_col = req.y_column or stage_col
    grouped = (
        _lf(dataset_id, req)
        .group_by(stage_col)
        .agg(_agg_expr(val_col, req.aggregation).alias("value"))
        .sort("value", descending=True)
        .limit(req.limit)
        .collect()
    )
    stages = grouped.to_dicts()
    max_v = float(stages[0]["value"]) if stages else 1.0
    data: list[ChartDataPoint] = []
    prev = max_v
    for i, row in enumerate(stages):
        v = float(row["value"] or 0)
        drop = ((prev - v) / prev * 100) if prev and i > 0 else 0.0
        data.append(
            ChartDataPoint(
                label=str(row[stage_col]),
                value=v,
                extra={"stage": i + 1, "drop_percent": round(drop, 2), "conversion": round(v / max_v * 100, 2)},
            )
        )
        prev = v
    return ChartResponse(chart_type="funnel", data=data, meta={"max": max_v})


def build_candlestick(dataset_id: str, req: ChartRequest) -> ChartResponse:
    cfg = req.config
    date_col = cfg.get("date_column") or req.x_column
    open_c = cfg.get("open_column") or "open"
    high_c = cfg.get("high_column") or "high"
    low_c = cfg.get("low_column") or "low"
    close_c = cfg.get("close_column") or req.y_column or "close"
    vol_c = cfg.get("volume_column")
    cols = [c for c in [date_col, open_c, high_c, low_c, close_c, vol_c] if c]
    df = _lf(dataset_id, req).select(cols).sort(date_col).limit(req.limit).collect()
    series = []
    for row in df.iter_rows(named=True):
        item = {
            "date": str(row[date_col]),
            "open": float(row.get(open_c) or 0),
            "high": float(row.get(high_c) or 0),
            "low": float(row.get(low_c) or 0),
            "close": float(row.get(close_c) or 0),
        }
        if vol_c and vol_c in row:
            item["volume"] = float(row[vol_c] or 0)
        series.append(item)
    return ChartResponse(chart_type="candlestick", data=[], series=series, meta={"ohlc": True})


def build_treemap(dataset_id: str, req: ChartRequest) -> ChartResponse:
    name_col = req.x_column
    parent_col = req.parent_column or req.config.get("parent_column")
    val_col = req.y_column or name_col
    if parent_col:
        grouped = (
            _lf(dataset_id, req)
            .group_by([parent_col, name_col])
            .agg(_agg_expr(val_col, req.aggregation).alias("value"))
            .limit(req.limit)
            .collect()
        )
        nodes = [
            ChartNode(
                id=f"{row[parent_col]}::{row[name_col]}",
                name=str(row[name_col]),
                parent=str(row[parent_col]),
                value=float(row["value"] or 0),
            )
            for row in grouped.iter_rows(named=True)
        ]
    else:
        grouped = (
            _lf(dataset_id, req)
            .group_by(name_col)
            .agg(_agg_expr(val_col, req.aggregation).alias("value"))
            .sort("value", descending=True)
            .limit(req.limit)
            .collect()
        )
        nodes = [
            ChartNode(id=str(row[name_col]), name=str(row[name_col]), value=float(row["value"] or 0))
            for row in grouped.iter_rows(named=True)
        ]
    return ChartResponse(chart_type="treemap", data=[], nodes=nodes)


def build_waterfall(dataset_id: str, req: ChartRequest) -> ChartResponse:
    grouped = (
        _lf(dataset_id, req)
        .group_by(req.x_column)
        .agg(_agg_expr(req.y_column or req.x_column, req.aggregation).alias("value"))
        .limit(req.limit)
        .collect()
    )
    cumulative = 0.0
    data: list[ChartDataPoint] = []
    for row in grouped.iter_rows(named=True):
        v = float(row["value"] or 0)
        cumulative += v
        data.append(
            ChartDataPoint(
                label=str(row[req.x_column]),
                value=v,
                extra={"cumulative": cumulative, "positive": v >= 0},
            )
        )
    return ChartResponse(chart_type="waterfall", data=data, meta={"total": cumulative})


def build_sunburst(dataset_id: str, req: ChartRequest) -> ChartResponse:
    resp = build_treemap(dataset_id, req)
    resp.chart_type = "sunburst"
    return resp


def build_network(dataset_id: str, req: ChartRequest) -> ChartResponse:
    resp = build_sankey(dataset_id, req)
    resp.chart_type = "network"
    return resp


def build_heatmap(dataset_id: str, req: ChartRequest) -> ChartResponse:
    y_col = req.y_column or req.x_column
    grouped = (
        _lf(dataset_id, req)
        .group_by([req.x_column, y_col])
        .agg(pl.len().alias("value"))
        .limit(req.limit)
        .collect()
    )
    data = [
        ChartDataPoint(
            label=f"{row[req.x_column]}|{row[y_col]}",
            value=float(row["value"] or 0),
            extra={"x": str(row[req.x_column]), "y": str(row[y_col])},
        )
        for row in grouped.iter_rows(named=True)
    ]
    return ChartResponse(chart_type="heatmap", data=data)


def build_boxplot(dataset_id: str, req: ChartRequest) -> ChartResponse:
    col = req.y_column or req.x_column
    stats = (
        _lf(dataset_id, req)
        .select(
            [
                pl.col(col).cast(pl.Float64).min().alias("min"),
                pl.col(col).cast(pl.Float64).quantile(0.25).alias("q1"),
                pl.col(col).cast(pl.Float64).median().alias("median"),
                pl.col(col).cast(pl.Float64).quantile(0.75).alias("q3"),
                pl.col(col).cast(pl.Float64).max().alias("max"),
            ]
        )
        .collect()
    )
    row = stats.to_dicts()[0] if stats.height else {}
    return ChartResponse(
        chart_type="boxplot",
        data=[],
        series=[row],
        meta={"column": col},
    )


def build_radar(dataset_id: str, req: ChartRequest) -> ChartResponse:
    return build_bar_line(dataset_id, req)


def _is_num(v: object) -> bool:
    try:
        float(v)  # type: ignore[arg-type]
        return True
    except (TypeError, ValueError):
        return False
