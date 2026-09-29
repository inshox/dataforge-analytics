"""Chart type registry — maps chart_type to builder functions."""

from __future__ import annotations

from typing import Callable

from app.models.schemas import ChartRequest, ChartResponse
from app.services.chart_engine import builders

ChartBuilder = Callable[[str, ChartRequest], ChartResponse]

REGISTRY: dict[str, ChartBuilder] = {
    "bar": builders.build_bar_line,
    "line": builders.build_bar_line,
    "area": builders.build_bar_line,
    "pie": builders.build_bar_line,
    "histogram": builders.build_bar_line,
    "scatter": builders.build_scatter,
    "bubble": builders.build_bubble,
    "sankey": builders.build_sankey,
    "funnel": builders.build_funnel,
    "candlestick": builders.build_candlestick,
    "treemap": builders.build_treemap,
    "waterfall": builders.build_waterfall,
    "sunburst": builders.build_sunburst,
    "network": builders.build_network,
    "heatmap": builders.build_heatmap,
    "boxplot": builders.build_boxplot,
    "gauge": builders.build_bar_line,
    "radar": builders.build_radar,
}


def build_chart(dataset_id: str, req: ChartRequest) -> ChartResponse:
    builder = REGISTRY.get(req.chart_type.lower())
    if not builder:
        builder = builders.build_bar_line
    return builder(dataset_id, req)


def list_chart_types() -> list[dict[str, str]]:
    return [
        {"id": k, "category": _category(k)}
        for k in sorted(REGISTRY.keys())
    ]


def _category(chart_type: str) -> str:
    if chart_type in ("sankey", "network", "funnel"):
        return "flow"
    if chart_type in ("candlestick", "waterfall"):
        return "finance"
    if chart_type in ("treemap", "sunburst"):
        return "hierarchy"
    return "standard"
