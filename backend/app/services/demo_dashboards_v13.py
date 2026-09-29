"""Seed v1.3 demo dashboards with variables and drill-through."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import DashboardRecord, DashboardWidgetRecord
from app.models.v12 import DashboardDrillthroughRuleRecord, DashboardVariableRecord
from app.services.dashboard_variable_service import DashboardVariableService
from app.models.schemas import DashboardVariableCreate

DEMO_EXECUTIVE_ID = "00000000-0000-4000-8000-000000000002"
DEMO_REGIONAL_ID = "00000000-0000-4000-8000-000000000003"
DEMO_CUSTOMER_ID = "00000000-0000-4000-8000-000000000004"


class DemoDashboardsV13:
    @staticmethod
    async def seed(session: AsyncSession, dataset_id: str) -> None:
        existing = await session.get(DashboardRecord, DEMO_EXECUTIVE_ID)
        if existing:
            return

        await DemoDashboardsV13._create_executive(session, dataset_id)
        await DemoDashboardsV13._create_regional(session, dataset_id)
        await DemoDashboardsV13._create_customer(session, dataset_id)
        await DemoDashboardsV13._create_drillthrough(session)
        await session.commit()

    @staticmethod
    async def _create_executive(session: AsyncSession, dataset_id: str) -> None:
        dash = DashboardRecord(
            id=DEMO_EXECUTIVE_ID,
            name="Demo — Executive Overview",
            description="Variables: date range, region, segment. Click charts to filter.",
        )
        session.add(dash)
        for var in [
            ("date_range", "Date Range", "date_range", "date", {"from": "2024-01-05", "to": "2024-01-20"}),
            ("region", "Region", "select", "region", "North"),
            ("segment", "Segment", "select", "category", "Electronics"),
        ]:
            session.add(
                DashboardVariableRecord(
                    id=str(uuid.uuid4()),
                    dashboard_id=DEMO_EXECUTIVE_ID,
                    name=var[0],
                    label=var[1],
                    var_type=var[2],
                    column_name=var[3],
                    dataset_id=dataset_id,
                    default_value_json=json.dumps(var[4]),
                    current_value_json=json.dumps(var[4]),
                )
            )
        widgets = [
            ("kpi", 0, 0, 3, 2, {"label": "Revenue", "metric_column": "revenue", "aggregation": "sum"}),
            ("kpi", 3, 0, 3, 2, {"label": "Profit KPI", "metric_column": "revenue", "aggregation": "sum"}),
            ("bar", 0, 2, 6, 4, {"x_column": "region", "y_column": "revenue", "aggregation": "sum",
             "variable_filters": [{"variable_id": "region", "column": "region", "operator": "eq"}]}),
            ("pie", 6, 2, 6, 4, {"x_column": "category", "y_column": "revenue", "aggregation": "sum",
             "variable_filters": [{"variable_id": "segment", "column": "category", "operator": "eq"}]}),
            ("line", 0, 6, 12, 4, {"x_column": "date", "y_column": "revenue", "aggregation": "sum"}),
        ]
        DemoDashboardsV13._add_widgets(session, DEMO_EXECUTIVE_ID, dataset_id, widgets)

    @staticmethod
    async def _create_regional(session: AsyncSession, dataset_id: str) -> None:
        dash = DashboardRecord(
            id=DEMO_REGIONAL_ID,
            name="Demo — Regional Detail",
            description="Drill target from Executive by region.",
        )
        session.add(dash)
        for var in [
            ("region", "Region", "select", "region", ""),
            ("date_range", "Date Range", "date_range", "date", {"from": "2024-01-05", "to": "2024-01-20"}),
        ]:
            session.add(
                DashboardVariableRecord(
                    id=str(uuid.uuid4()),
                    dashboard_id=DEMO_REGIONAL_ID,
                    name=var[0],
                    label=var[1],
                    var_type=var[2],
                    column_name=var[3],
                    dataset_id=dataset_id,
                    default_value_json=json.dumps(var[4]),
                    current_value_json=json.dumps(var[4]),
                )
            )
        widgets = [
            ("line", 0, 0, 8, 4, {"x_column": "date", "y_column": "revenue", "aggregation": "sum"}),
            ("bar", 8, 0, 4, 4, {"x_column": "product", "y_column": "revenue", "aggregation": "sum"}),
            ("table", 0, 4, 12, 3, {"limit": 8}),
        ]
        DemoDashboardsV13._add_widgets(session, DEMO_REGIONAL_ID, dataset_id, widgets)

    @staticmethod
    async def _create_customer(session: AsyncSession, dataset_id: str) -> None:
        dash = DashboardRecord(
            id=DEMO_CUSTOMER_ID,
            name="Demo — Customer Detail",
            description="Product-level detail; drill by product as customer proxy.",
        )
        session.add(dash)
        for var in [
            ("customer_id", "Customer / Product", "select", "product", ""),
            ("date_range", "Date Range", "date_range", "date", {"from": "2024-01-05", "to": "2024-01-20"}),
        ]:
            session.add(
                DashboardVariableRecord(
                    id=str(uuid.uuid4()),
                    dashboard_id=DEMO_CUSTOMER_ID,
                    name=var[0],
                    label=var[1],
                    var_type=var[2],
                    column_name=var[3],
                    dataset_id=dataset_id,
                    default_value_json=json.dumps(var[4]),
                    current_value_json=json.dumps(var[4]),
                )
            )
        widgets = [
            ("kpi", 0, 0, 4, 2, {"label": "Customer Revenue", "metric_column": "revenue", "aggregation": "sum"}),
            ("bar", 4, 0, 8, 4, {"x_column": "date", "y_column": "revenue", "aggregation": "sum"}),
            ("pie", 0, 2, 6, 4, {"x_column": "category", "y_column": "revenue", "aggregation": "sum"}),
        ]
        DemoDashboardsV13._add_widgets(session, DEMO_CUSTOMER_ID, dataset_id, widgets)

    @staticmethod
    def _add_widgets(session, dashboard_id, dataset_id, widgets):
        for wtype, x, y, w, h, settings in widgets:
            session.add(
                DashboardWidgetRecord(
                    id=str(uuid.uuid4()),
                    dashboard_id=dashboard_id,
                    widget_type=wtype,
                    dataset_id=dataset_id,
                    chart_type=wtype if wtype not in ("kpi", "table") else None,
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    settings_json=json.dumps(settings),
                )
            )

    @staticmethod
    async def _create_drillthrough(session: AsyncSession) -> None:
        rules = [
            (DEMO_EXECUTIVE_ID, DEMO_REGIONAL_ID, "region", "region", "View region detail"),
            (DEMO_EXECUTIVE_ID, DEMO_CUSTOMER_ID, "product", "customer_id", "View customer detail"),
            (DEMO_REGIONAL_ID, DEMO_CUSTOMER_ID, "product", "customer_id", "View customer"),
        ]
        for src, tgt, col, var_name, label in rules:
            session.add(
                DashboardDrillthroughRuleRecord(
                    id=str(uuid.uuid4()),
                    source_dashboard_id=src,
                    target_dashboard_id=tgt,
                    trigger_column=col,
                    target_variable_name=var_name,
                    label=label,
                    open_mode="tab",
                )
            )
