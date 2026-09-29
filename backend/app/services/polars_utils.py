"""Shared Polars helpers."""

import json
from pathlib import Path
from typing import Any

import polars as pl

from app.models.schemas import ColumnInfo, FilterCondition, FilterOperator, SortSpec


def infer_columns(df: pl.DataFrame) -> list[ColumnInfo]:
    return [
        ColumnInfo(name=c, dtype=str(df.schema[c]), nullable=df[c].null_count() > 0)
        for c in df.columns
    ]


def columns_from_json(raw: str | None) -> list[ColumnInfo]:
    if not raw:
        return []
    data = json.loads(raw)
    return [ColumnInfo(**item) for item in data]


def columns_to_json(columns: list[ColumnInfo]) -> str:
    return json.dumps([c.model_dump() for c in columns])


def load_lazy(parquet: Path) -> pl.LazyFrame:
    return pl.scan_parquet(str(parquet))


def load_frame(parquet: Path) -> pl.DataFrame:
    return pl.read_parquet(str(parquet))


def apply_filters(lf: pl.LazyFrame, filters: list[FilterCondition], global_search: str | None) -> pl.LazyFrame:
    for f in filters:
        col = pl.col(f.column)
        op = f.operator
        if op == FilterOperator.is_empty:
            lf = lf.filter(col.is_null() | (col.cast(pl.Utf8) == ""))
        elif op == FilterOperator.is_not_empty:
            lf = lf.filter(col.is_not_null() & (col.cast(pl.Utf8) != ""))
        elif op == FilterOperator.equals:
            lf = lf.filter(col == f.value)
        elif op == FilterOperator.not_equals:
            lf = lf.filter(col != f.value)
        elif op == FilterOperator.greater_or_equal:
            lf = lf.filter(col >= f.value)
        elif op == FilterOperator.less_or_equal:
            lf = lf.filter(col <= f.value)
        elif op == FilterOperator.in_list:
            vals = f.value if isinstance(f.value, list) else [f.value]
            lf = lf.filter(col.is_in(vals))
        elif op == FilterOperator.contains:
            lf = lf.filter(col.cast(pl.Utf8).str.contains(str(f.value or ""), literal=False))
        elif op == FilterOperator.starts_with:
            lf = lf.filter(col.cast(pl.Utf8).str.starts_with(str(f.value or "")))
        elif op == FilterOperator.greater_than:
            lf = lf.filter(col > f.value)
        elif op == FilterOperator.less_than:
            lf = lf.filter(col < f.value)
        elif op == FilterOperator.between and f.value is not None and f.value_to is not None:
            lf = lf.filter((col >= f.value) & (col <= f.value_to))
    if global_search:
        # OR across string columns — collect schema from lazy frame is expensive; use all cols as utf8 try
        lf_cols = lf.collect_schema().names()
        exprs = [pl.col(c).cast(pl.Utf8).str.contains(global_search, literal=False) for c in lf_cols]
        if exprs:
            combined = exprs[0]
            for e in exprs[1:]:
                combined = combined | e
            lf = lf.filter(combined)
    return lf


def apply_sort(lf: pl.LazyFrame, sort: list[SortSpec]) -> pl.LazyFrame:
    if not sort:
        return lf
    by = [s.column for s in sort]
    descending = [s.descending for s in sort]
    return lf.sort(by, descending=descending)


def df_to_records(df: pl.DataFrame) -> list[dict[str, Any]]:
    return df.to_dicts()


def detect_csv_separator(sample: bytes) -> str:
    for sep in (",", ";", "\t", "|"):
        if sample.count(sep.encode() if isinstance(sep, str) else sep) > 2:
            return sep
    return ","
