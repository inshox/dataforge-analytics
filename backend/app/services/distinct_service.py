"""Distinct column values via DuckDB on Parquet."""

from __future__ import annotations

import duckdb

from app.core.storage import parquet_path
from app.models.schemas import DistinctValuesResponse


class DistinctService:
    @staticmethod
    def distinct_values(dataset_id: str, column_name: str, limit: int = 500) -> DistinctValuesResponse:
        pq = parquet_path(dataset_id)
        if not pq.exists():
            raise ValueError("Dataset not found")

        path = str(pq).replace("\\", "/").replace("'", "''")
        col = column_name.replace('"', "")
        limit = min(max(limit, 1), 2000)

        sql = f'''
            SELECT DISTINCT CAST("{col}" AS VARCHAR) AS v
            FROM read_parquet('{path}')
            WHERE "{col}" IS NOT NULL
            ORDER BY v
            LIMIT {limit}
        '''
        con = duckdb.connect(database=":memory:")
        rows = con.execute(sql).fetchall()
        values = [str(r[0]) for r in rows if r[0] is not None]
        return DistinctValuesResponse(dataset_id=dataset_id, column=column_name, values=values)
