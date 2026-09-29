"""Dashboard templates — Executive, Finance, Sales, etc."""

from __future__ import annotations

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import DashboardRecord, DashboardWidgetRecord
from app.models.schemas import DashboardDetail, DashboardTemplateSummary

TEMPLATES: list[dict] = [
    {
        "id": "tpl-executive",
        "name": "Executive Overview",
        "category": "executive",
        "description": "KPIs, trends, and regional breakdown.",
        "widgets": [
            ("kpi", 0, 0, 3, 2, {}),
            ("kpi", 3, 0, 3, 2, {}),
            ("line", 0, 2, 8, 4, {}),
            ("bar", 8, 2, 4, 4, {}),
        ],
    },
    {
        "id": "tpl-finance",
        "name": "Finance",
        "category": "finance",
        "description": "Waterfall, KPIs, and variance charts.",
        "widgets": [
            ("waterfall", 0, 0, 8, 4, {}),
            ("kpi", 8, 0, 4, 2, {}),
            ("bar", 8, 2, 4, 4, {}),
        ],
    },
    {
        "id": "tpl-sales",
        "name": "Sales",
        "category": "sales",
        "description": "Funnel, top performers, regional heatmap.",
        "widgets": [
            ("funnel", 0, 0, 4, 5, {}),
            ("bar", 4, 0, 8, 3, {}),
            ("heatmap", 4, 3, 8, 3, {}),
        ],
    },
    {
        "id": "tpl-marketing",
        "name": "Marketing",
        "category": "marketing",
        "description": "Sankey flows and campaign KPIs.",
        "widgets": [
            ("sankey", 0, 0, 12, 5, {}),
            ("kpi", 0, 5, 4, 2, {}),
            ("pie", 4, 5, 4, 2, {}),
        ],
    },
    {
        "id": "tpl-operations",
        "name": "Operations",
        "category": "operations",
        "description": "Throughput, anomalies, and gauges.",
        "widgets": [
            ("line", 0, 0, 6, 4, {}),
            ("gauge", 6, 0, 3, 4, {}),
            ("table", 9, 0, 3, 4, {}),
        ],
    },
    {
        "id": "tpl-inventory",
        "name": "Inventory",
        "category": "inventory",
        "description": "Treemap and stock KPIs.",
        "widgets": [
            ("treemap", 0, 0, 8, 5, {}),
            ("kpi", 8, 0, 4, 2, {}),
            ("bar", 8, 2, 4, 3, {}),
        ],
    },
]


class DashboardTemplateService:
    @staticmethod
    def list_templates() -> list[DashboardTemplateSummary]:
        return [
            DashboardTemplateSummary(
                id=t["id"],
                name=t["name"],
                category=t["category"],
                description=t["description"],
                widget_count=len(t["widgets"]),
            )
            for t in TEMPLATES
        ]

    @staticmethod
    async def instantiate(
        session: AsyncSession,
        template_id: str,
        dataset_id: str,
        name: str | None = None,
    ) -> DashboardDetail:
        tpl = next((t for t in TEMPLATES if t["id"] == template_id), None)
        if not tpl:
            raise ValueError("Template not found")

        dash = DashboardRecord(
            id=str(uuid.uuid4()),
            name=name or tpl["name"],
            description=tpl["description"],
        )
        session.add(dash)
        for wtype, x, y, w, h, extra in tpl["widgets"]:
            settings = {
                "x_column": "",
                "y_column": "",
                "aggregation": "sum",
                **extra,
            }
            session.add(
                DashboardWidgetRecord(
                    id=str(uuid.uuid4()),
                    dashboard_id=dash.id,
                    widget_type=wtype,
                    dataset_id=dataset_id,
                    chart_type=wtype if wtype not in ("kpi", "table", "gauge") else None,
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    settings_json=json.dumps(settings),
                )
            )
        await session.commit()
        from app.services.dashboard_service import DashboardService

        detail = await DashboardService.get_dashboard(session, dash.id)
        assert detail is not None
        return detail
