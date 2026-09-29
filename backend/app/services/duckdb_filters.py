"""Build DuckDB WHERE clauses from filter conditions."""

from __future__ import annotations

from app.models.schemas import FilterCondition, FilterOperator


def _lit(v: object) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("'", "''")
    return f"'{s}'"


def filters_to_where(filters: list[FilterCondition]) -> str:
    parts: list[str] = []
    for f in filters:
        col = f.column.replace('"', "")
        c = f'"{col}"'
        op = f.operator
        if op == FilterOperator.is_empty:
            parts.append(f"({c} IS NULL OR CAST({c} AS VARCHAR) = '')")
        elif op == FilterOperator.is_not_empty:
            parts.append(f"({c} IS NOT NULL AND CAST({c} AS VARCHAR) != '')")
        elif op == FilterOperator.equals:
            parts.append(f"{c} = {_lit(f.value)}")
        elif op == FilterOperator.not_equals:
            parts.append(f"{c} != {_lit(f.value)}")
        elif op == FilterOperator.contains:
            parts.append(f"CAST({c} AS VARCHAR) ILIKE '%' || {_lit(f.value)} || '%'")
        elif op == FilterOperator.starts_with:
            parts.append(f"CAST({c} AS VARCHAR) ILIKE {_lit(str(f.value) + '%')}")
        elif op == FilterOperator.greater_than:
            parts.append(f"TRY_CAST({c} AS DOUBLE) > {_lit(f.value)}")
        elif op == FilterOperator.less_than:
            parts.append(f"TRY_CAST({c} AS DOUBLE) < {_lit(f.value)}")
        elif op == FilterOperator.greater_or_equal:
            parts.append(f"TRY_CAST({c} AS DOUBLE) >= {_lit(f.value)}")
        elif op == FilterOperator.less_or_equal:
            parts.append(f"TRY_CAST({c} AS DOUBLE) <= {_lit(f.value)}")
        elif op == FilterOperator.between:
            parts.append(f"TRY_CAST({c} AS DOUBLE) BETWEEN {_lit(f.value)} AND {_lit(f.value_to)}")
        elif op == FilterOperator.in_list:
            vals = f.value if isinstance(f.value, list) else [f.value]
            inner = ", ".join(_lit(v) for v in vals)
            parts.append(f"CAST({c} AS VARCHAR) IN ({inner})")
    if not parts:
        return ""
    return "WHERE " + " AND ".join(parts)
