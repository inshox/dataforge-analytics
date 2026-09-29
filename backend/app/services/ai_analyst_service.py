"""Natural-language questions → DuckDB SQL (local heuristic analyst)."""

from __future__ import annotations

import re

from app.models.schemas import AiAnalystResponse, ColumnInfo
from app.services.sql_service import SqlService


class AiAnalystService:
    @staticmethod
    def analyze(
        dataset_id: str,
        question: str,
        columns: list[ColumnInfo],
    ) -> AiAnalystResponse:
        q = question.strip().lower()
        col_names = [c.name for c in columns]
        numeric = [
            c.name
            for c in columns
            if any(t in c.dtype.lower() for t in ("int", "float", "decimal", "numeric"))
        ]
        text_cols = [c.name for c in columns if c.name not in numeric]

        sql, explanation, chart_type, x_col, y_col = _heuristic_sql(
            q, col_names, numeric, text_cols
        )
        quality = _data_quality_notes(columns)
        layout = _suggest_dashboard_layout(chart_type, x_col, y_col)
        summary = _executive_summary(q, columns, numeric)

        return AiAnalystResponse(
            sql=sql,
            explanation=explanation,
            suggested_chart_type=chart_type,
            suggested_x_column=x_col,
            suggested_y_column=y_col,
            executive_summary=summary,
            data_quality_notes=quality,
            suggested_dashboard_layout=layout,
        )

    @staticmethod
    def execute(dataset_id: str, sql: str, page: int = 1, page_size: int = 100):
        return SqlService.execute(dataset_id, sql, page, page_size)


def _pick_col(candidates: list[str], keywords: list[str], fallback: list[str]) -> str | None:
    for kw in keywords:
        for c in candidates:
            if kw in c.lower():
                return c
    return fallback[0] if fallback else None


def _data_quality_notes(columns: list[ColumnInfo]) -> list[str]:
    notes: list[str] = []
    for c in columns:
        if c.nullable:
            notes.append(f"Column '{c.name}' may contain nulls — filter or impute before KPIs.")
    if len(columns) < 3:
        notes.append("Dataset has few columns; joins or enrichments may be needed.")
    return notes[:5]


def _suggest_dashboard_layout(
    chart_type: str | None, x_col: str | None, y_col: str | None
) -> list[str]:
    layout = ["Row 1: two KPI widgets (primary metrics)"]
    if chart_type == "line" and x_col:
        layout.append(f"Row 2: line chart — {y_col or 'value'} over {x_col}")
    elif chart_type == "bar" and x_col:
        layout.append(f"Row 2: bar chart — {y_col or 'value'} by {x_col}")
    else:
        layout.append("Row 2: bar or pie chart for top dimension")
    layout.append("Row 3: table or anomaly feed for detail")
    return layout


def _executive_summary(
    question: str, columns: list[ColumnInfo], numeric: list[str]
) -> str:
    ncol = len(columns)
    nn = len(numeric)
    return (
        f"Local analysis for: “{question[:120]}”. "
        f"Dataset has {ncol} columns ({nn} numeric). "
        "Results are computed entirely on-device; no data leaves this machine."
    )


def _heuristic_sql(
    q: str,
    all_cols: list[str],
    numeric: list[str],
    text_cols: list[str],
) -> tuple[str, str, str | None, str | None, str | None]:
    limit = 10
    m = re.search(r"(?:top|first|last)\s+(\d+)", q)
    if m:
        limit = min(int(m.group(1)), 1000)
    m = re.search(r"(\d+)\s+(?:rows|records)", q)
    if m and "top" in q:
        limit = min(int(m.group(1)), 1000)

    revenue_col = _pick_col(numeric, ["revenue", "amount", "total", "sales", "price"], numeric)
    count_col = _pick_col(numeric, ["count", "qty", "quantity", "units"], numeric)
    group_col = _pick_col(
        text_cols,
        ["region", "category", "product", "country", "city", "name", "type", "segment"],
        text_cols,
    )
    date_col = _pick_col(all_cols, ["date", "time", "month", "year"], all_cols)

    if any(w in q for w in ("how many", "count rows", "total rows", "number of rows")):
        sql = "SELECT COUNT(*) AS row_count FROM dataset"
        return sql, "Counts all rows in the dataset.", "bar", None, "row_count"

    if "duplicate" in q:
        sql = "SELECT * FROM dataset LIMIT 100"
        return (
            sql,
            "Shows sample rows; use Analysis tab for duplicate statistics.",
            None,
            None,
            None,
        )

    if any(w in q for w in ("average", "avg", "mean")) and revenue_col:
        sql = f'SELECT AVG("{revenue_col}") AS average_{revenue_col} FROM dataset'
        return sql, f"Average of {revenue_col}.", "bar", None, f"average_{revenue_col}"

    if any(w in q for w in ("sum", "total")) and revenue_col:
        sql = f'SELECT SUM("{revenue_col}") AS total_{revenue_col} FROM dataset'
        return sql, f"Sum of {revenue_col}.", "bar", None, f"total_{revenue_col}"

    if any(w in q for w in ("group", "by", "breakdown", "per")) and group_col:
        agg = f'SUM("{revenue_col}")' if revenue_col else "COUNT(*)"
        label = revenue_col or "count"
        sql = (
            f'SELECT "{group_col}", {agg} AS {label} FROM dataset '
            f'GROUP BY "{group_col}" ORDER BY {label} DESC LIMIT {limit}'
        )
        return (
            sql,
            f"Groups by {group_col} with aggregation.",
            "bar",
            group_col,
            label,
        )

    if any(w in q for w in ("top", "highest", "best", "largest")) and revenue_col:
        sql = (
            f'SELECT * FROM dataset ORDER BY "{revenue_col}" DESC LIMIT {limit}'
        )
        return sql, f"Top {limit} rows by {revenue_col}.", "bar", revenue_col, revenue_col

    if any(w in q for w in ("lowest", "bottom", "smallest")) and revenue_col:
        sql = (
            f'SELECT * FROM dataset ORDER BY "{revenue_col}" ASC LIMIT {limit}'
        )
        return sql, f"Bottom {limit} rows by {revenue_col}.", "bar", revenue_col, revenue_col

    if any(w in q for w in ("trend", "over time", "by month", "by date")) and date_col and revenue_col:
        sql = (
            f'SELECT "{date_col}", SUM("{revenue_col}") AS total FROM dataset '
            f'GROUP BY "{date_col}" ORDER BY "{date_col}" LIMIT {limit}'
        )
        return sql, f"Trend of {revenue_col} over {date_col}.", "line", date_col, "total"

    if "null" in q or "missing" in q:
        parts = [f'SUM(CASE WHEN "{c}" IS NULL THEN 1 ELSE 0 END) AS "{c}_nulls"' for c in all_cols[:15]]
        sql = f"SELECT {', '.join(parts)} FROM dataset"
        return sql, "Null counts per column.", "bar", None, None

    if "show" in q or "preview" in q or "sample" in q or "all" in q:
        sql = f"SELECT * FROM dataset LIMIT {limit}"
        return sql, f"Preview of first {limit} rows.", None, None, None

    # Default: show columns overview
    sql = f"SELECT * FROM dataset LIMIT {limit}"
    return (
        sql,
        "General preview. Try: 'top 10 by revenue', 'count by region', 'average price'.",
        None,
        None,
        None,
    )
