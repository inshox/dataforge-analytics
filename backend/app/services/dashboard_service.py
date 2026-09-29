"""Dashboard CRUD and widget persistence."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import DashboardRecord, DashboardWidgetRecord
from app.models.schemas import (
    DashboardCreate,
    DashboardDetail,
    DashboardSaveBody,
    DashboardSummary,
    DashboardWidgetSpec,
)
class DashboardService:
    @staticmethod
    async def list_dashboards(session: AsyncSession) -> list[DashboardSummary]:
        q = (
            select(
                DashboardRecord,
                func.count(DashboardWidgetRecord.id).label("wc"),
            )
            .outerjoin(DashboardWidgetRecord, DashboardWidgetRecord.dashboard_id == DashboardRecord.id)
            .group_by(DashboardRecord.id)
            .order_by(DashboardRecord.updated_at.desc())
        )
        rows = await session.execute(q)
        out: list[DashboardSummary] = []
        for rec, wc in rows.all():
            out.append(
                DashboardSummary(
                    id=rec.id,
                    name=rec.name,
                    description=rec.description,
                    widget_count=int(wc or 0),
                    created_at=rec.created_at.isoformat() if rec.created_at else None,
                    updated_at=rec.updated_at.isoformat() if rec.updated_at else None,
                )
            )
        return out

    @staticmethod
    async def get_dashboard(session: AsyncSession, dashboard_id: str) -> DashboardDetail | None:
        rec = await session.get(DashboardRecord, dashboard_id)
        if not rec:
            return None
        widgets = await DashboardService._load_widgets(session, dashboard_id)
        return DashboardDetail(
            id=rec.id,
            name=rec.name,
            description=rec.description,
            widget_count=len(widgets),
            layout_json=rec.layout_json,
            widgets=widgets,
            created_at=rec.created_at.isoformat() if rec.created_at else None,
            updated_at=rec.updated_at.isoformat() if rec.updated_at else None,
        )

    @staticmethod
    async def create_dashboard(session: AsyncSession, body: DashboardCreate) -> DashboardDetail:
        rec = DashboardRecord(id=str(uuid.uuid4()), name=body.name, description=body.description)
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return DashboardDetail(
            id=rec.id,
            name=rec.name,
            description=rec.description,
            widget_count=0,
            widgets=[],
            created_at=rec.created_at.isoformat() if rec.created_at else None,
            updated_at=rec.updated_at.isoformat() if rec.updated_at else None,
        )

    @staticmethod
    async def update_dashboard(
        session: AsyncSession, dashboard_id: str, body: DashboardSaveBody
    ) -> DashboardDetail | None:
        rec = await session.get(DashboardRecord, dashboard_id)
        if not rec:
            return None
        if body.name is not None:
            rec.name = body.name
        if body.description is not None:
            rec.description = body.description
        if body.layout_json is not None:
            rec.layout_json = body.layout_json

        await session.execute(
            delete(DashboardWidgetRecord).where(DashboardWidgetRecord.dashboard_id == dashboard_id)
        )
        for w in body.widgets:
            session.add(
                DashboardWidgetRecord(
                    id=w.id or str(uuid.uuid4()),
                    dashboard_id=dashboard_id,
                    widget_type=w.widget_type,
                    dataset_id=w.dataset_id,
                    chart_type=w.chart_type,
                    sql_query=w.sql_query,
                    x=w.x,
                    y=w.y,
                    w=w.w,
                    h=w.h,
                    settings_json=json.dumps(w.settings),
                )
            )
        await session.commit()
        return await DashboardService.get_dashboard(session, dashboard_id)

    @staticmethod
    async def delete_dashboard(session: AsyncSession, dashboard_id: str) -> bool:
        rec = await session.get(DashboardRecord, dashboard_id)
        if not rec:
            return False
        await session.delete(rec)
        await session.commit()
        return True

    @staticmethod
    async def duplicate_dashboard(session: AsyncSession, dashboard_id: str) -> DashboardDetail | None:
        detail = await DashboardService.get_dashboard(session, dashboard_id)
        if not detail:
            return None
        new_id = str(uuid.uuid4())
        rec = DashboardRecord(
            id=new_id,
            name=f"{detail.name} (copy)",
            description=detail.description,
            layout_json=detail.layout_json,
        )
        session.add(rec)
        for w in detail.widgets:
            session.add(
                DashboardWidgetRecord(
                    dashboard_id=new_id,
                    widget_type=w.widget_type,
                    dataset_id=w.dataset_id,
                    chart_type=w.chart_type,
                    sql_query=w.sql_query,
                    x=w.x,
                    y=w.y,
                    w=w.w,
                    h=w.h,
                    settings_json=json.dumps(w.settings),
                )
            )
        await session.commit()
        return await DashboardService.get_dashboard(session, new_id)

    @staticmethod
    def export_pdf(dashboard: DashboardDetail) -> bytes:
        from io import BytesIO

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"Dashboard: {dashboard.name}", styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"Widgets: {dashboard.widget_count}", styles["Normal"]),
        ]
        for w in dashboard.widgets:
            story.append(Spacer(1, 8))
            story.append(
                Paragraph(
                    f"• {w.widget_type} — dataset {w.dataset_id or 'n/a'} — {w.chart_type or ''}",
                    styles["Normal"],
                )
            )
        doc.build(story)
        return buf.getvalue()

    @staticmethod
    def export_html(dashboard: DashboardDetail) -> str:
        widgets = "".join(
            f"<li>{w.widget_type} ({w.w}x{w.h} at {w.x},{w.y})</li>" for w in dashboard.widgets
        )
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><title>{dashboard.name}</title></head>
<body><h1>{dashboard.name}</h1><ul>{widgets}</ul></body></html>"""

    @staticmethod
    async def _load_widgets(session: AsyncSession, dashboard_id: str) -> list[DashboardWidgetSpec]:
        result = await session.execute(
            select(DashboardWidgetRecord).where(DashboardWidgetRecord.dashboard_id == dashboard_id)
        )
        specs: list[DashboardWidgetSpec] = []
        for row in result.scalars().all():
            specs.append(
                DashboardWidgetSpec(
                    id=row.id,
                    widget_type=row.widget_type,
                    dataset_id=row.dataset_id,
                    chart_type=row.chart_type,
                    sql_query=row.sql_query,
                    x=row.x,
                    y=row.y,
                    w=row.w,
                    h=row.h,
                    settings=json.loads(row.settings_json or "{}"),
                )
            )
        return specs
