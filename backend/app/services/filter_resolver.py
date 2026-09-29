"""Resolve dashboard variables + widget bindings into FilterCondition list."""

from __future__ import annotations

from typing import Any

from app.models.schemas import DashboardVariableResponse, FilterCondition, FilterOperator, WidgetVariableFilter

_OP_MAP = {
    "eq": FilterOperator.equals,
    "equals": FilterOperator.equals,
    "neq": FilterOperator.not_equals,
    "not_equals": FilterOperator.not_equals,
    "gt": FilterOperator.greater_than,
    "greater_than": FilterOperator.greater_than,
    "lt": FilterOperator.less_than,
    "less_than": FilterOperator.less_than,
    "gte": FilterOperator.greater_or_equal,
    "greater_or_equal": FilterOperator.greater_or_equal,
    "lte": FilterOperator.less_or_equal,
    "less_or_equal": FilterOperator.less_or_equal,
    "in": FilterOperator.in_list,
    "in_list": FilterOperator.in_list,
    "between": FilterOperator.between,
    "contains": FilterOperator.contains,
}


def merge_filters(*groups: list[FilterCondition]) -> list[FilterCondition]:
    out: list[FilterCondition] = []
    for g in groups:
        out.extend(g)
    return out


def variables_to_filters(variables: list[DashboardVariableResponse]) -> list[FilterCondition]:
    filters: list[FilterCondition] = []
    for var in variables:
        col = var.column_name or var.name
        val = var.current_value if var.current_value is not None else var.default_value
        if val is None or val == "" or val == []:
            continue
        vtype = var.type.lower()
        if vtype == "date_range" and isinstance(val, dict):
            if val.get("from") is not None and val.get("to") is not None:
                filters.append(
                    FilterCondition(
                        column=col,
                        operator=FilterOperator.between,
                        value=val["from"],
                        value_to=val["to"],
                    )
                )
            continue
        if vtype == "multi_select":
            if isinstance(val, list) and val:
                filters.append(
                    FilterCondition(column=col, operator=FilterOperator.in_list, value=val)
                )
            continue
        if vtype == "boolean":
            filters.append(
                FilterCondition(column=col, operator=FilterOperator.equals, value=bool(val))
            )
            continue
        filters.append(
            FilterCondition(column=col, operator=FilterOperator.equals, value=val)
        )
    return filters


def bindings_to_filters(
    bindings: list[WidgetVariableFilter],
    variables: list[DashboardVariableResponse],
) -> list[FilterCondition]:
    by_id = {v.id: v for v in variables}
    by_name = {v.name: v for v in variables}
    filters: list[FilterCondition] = []
    for b in bindings:
        var = by_id.get(b.variable_id) or by_name.get(b.variable_id)
        if not var:
            continue
        val = var.current_value if var.current_value is not None else var.default_value
        if val is None or val == "" or val == []:
            continue
        op = _OP_MAP.get(b.operator.lower(), FilterOperator.equals)
        col = b.column or var.column_name or var.name
        if op == FilterOperator.between and isinstance(val, dict):
            filters.append(
                FilterCondition(
                    column=col,
                    operator=op,
                    value=val.get("from"),
                    value_to=val.get("to"),
                )
            )
        elif op == FilterOperator.in_list:
            filters.append(
                FilterCondition(
                    column=col,
                    operator=op,
                    value=val if isinstance(val, list) else [val],
                )
            )
        else:
            filters.append(FilterCondition(column=col, operator=op, value=val))
    return filters


def parse_widget_bindings(settings: dict[str, Any]) -> list[WidgetVariableFilter]:
    raw = settings.get("variable_filters") or settings.get("filters") or []
    out: list[WidgetVariableFilter] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(WidgetVariableFilter(**item))
    return out
