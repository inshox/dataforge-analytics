"""Fast group-by aggregations via DuckDB on Parquet (5M+ row safe)."""

from __future__ import annotations

from typing import Any

import duckdb

from app.core.storage import parquet_path
from app.models.schemas import AggregateRequest, AggregateResponse, FilterCondition
from app.services.duckdb_filters import filters_to_where


class AggregateService:
    @staticmethod
    def aggregate(
        dataset_id: str,
        req: AggregateRequest,
        limit: int = 2000,
        extra_filters: list[FilterCondition] | None = None,
    ) -> AggregateResponse:
        pq = parquet_path(dataset_id)
        if not pq.exists():
            raise ValueError("Dataset parquet not found")

        if not req.aggregations:
            raise ValueError("At least one aggregation required")

        path = str(pq).replace("\\", "/").replace("'", "''")
        where = filters_to_where(extra_filters or [])
        group_cols = ", ".join(f'"{c}"' for c in req.group_by)
        group_clause = f"GROUP BY {group_cols}" if group_cols else ""
        select_parts = [group_cols] if group_cols else []

        for col, agg in req.aggregations.items():
            fn = agg.lower()
            if fn == "mean":
                fn = "avg"
            if fn not in ("sum", "avg", "count", "min", "max", "count_distinct", "median"):
                raise ValueError(f"Unsupported aggregation: {agg}")
            if fn == "count":
                expr = "COUNT(*)"
            elif fn == "count_distinct":
                expr = f'COUNT(DISTINCT "{col}")'
            elif fn == "median":
                expr = f'quantile_cont(TRY_CAST("{col}" AS DOUBLE), 0.5)'
            else:
                expr = f'{fn.upper()}(TRY_CAST("{col}" AS DOUBLE))'
            select_parts.append(f'{expr} AS "{col}_{fn}"')

        select_sql = ", ".join(select_parts)
        limit = min(max(limit, 1), 5000)
        sql = f"""
            SELECT {select_sql}
            FROM read_parquet('{path}')
            {where}
            {group_clause}
            LIMIT {limit}
        """

        con = duckdb.connect(database=":memory:")
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows_raw = cur.fetchall()
        rows: list[dict[str, Any]] = [dict(zip(cols, row)) for row in rows_raw]

        return AggregateResponse(dataset_id=dataset_id, rows=rows, columns=cols)
