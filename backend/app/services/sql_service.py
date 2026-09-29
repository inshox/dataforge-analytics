"""DuckDB SQL Lab over Parquet datasets."""

import math
from pathlib import Path

import duckdb
import polars as pl

from app.core.storage import parquet_path
from app.models.schemas import SqlResponse


class SqlService:
    @staticmethod
    def execute(dataset_id: str, query: str, page: int, page_size: int) -> SqlResponse:
        pq = parquet_path(dataset_id)
        if not pq.exists():
            raise ValueError("Dataset parquet not found")

        con = duckdb.connect(database=":memory:")
        con.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{_escape_path(pq)}')")

        # Safety: only allow SELECT
        normalized = query.strip().lower()
        if not normalized.startswith("select"):
            raise ValueError("Only SELECT queries are allowed")

        arrow = con.execute(query).fetch_arrow_table()
        full = pl.from_arrow(arrow)
        total = full.height
        offset = (page - 1) * page_size
        page_df = full.slice(offset, page_size)
        rows = page_df.to_dicts()
        columns = full.columns

        return SqlResponse(
            columns=columns,
            rows=rows,
            page=page,
            page_size=page_size,
            total_rows=total,
        )


def _escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")
