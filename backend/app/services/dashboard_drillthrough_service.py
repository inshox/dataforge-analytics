"""Dashboard drill-through rules."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    DashboardDrillthroughCreate,
    DashboardDrillthroughResponse,
    DashboardDrillthroughUpdate,
)
from app.models.v12 import DashboardDrillthroughRuleRecord


class DashboardDrillthroughService:
    @staticmethod
    def _to_response(rec: DashboardDrillthroughRuleRecord) -> DashboardDrillthroughResponse:
        return DashboardDrillthroughResponse(
            id=rec.id,
            source_dashboard_id=rec.source_dashboard_id,
            source_widget_id=rec.source_widget_id,
            target_dashboard_id=rec.target_dashboard_id,
            trigger_column=rec.trigger_column,
            target_variable_name=rec.target_variable_name,
            label=rec.label or "",
            open_mode=rec.open_mode or "tab",
            created_at=rec.created_at.isoformat() if rec.created_at else None,
        )

    @staticmethod
    async def list_rules(
        session: AsyncSession, dashboard_id: str
    ) -> list[DashboardDrillthroughResponse]:
        q = select(DashboardDrillthroughRuleRecord).where(
            DashboardDrillthroughRuleRecord.source_dashboard_id == dashboard_id
        )
        rows = (await session.execute(q)).scalars().all()
        return [DashboardDrillthroughService._to_response(r) for r in rows]

    @staticmethod
    async def create_rule(
        session: AsyncSession, dashboard_id: str, body: DashboardDrillthroughCreate
    ) -> DashboardDrillthroughResponse:
        rec = DashboardDrillthroughRuleRecord(
            id=str(uuid.uuid4()),
            source_dashboard_id=dashboard_id,
            source_widget_id=body.source_widget_id,
            target_dashboard_id=body.target_dashboard_id,
            trigger_column=body.trigger_column,
            target_variable_name=body.target_variable_name,
            label=body.label or body.target_variable_name,
            open_mode=body.open_mode,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return DashboardDrillthroughService._to_response(rec)

    @staticmethod
    async def update_rule(
        session: AsyncSession, dashboard_id: str, rule_id: str, body: DashboardDrillthroughUpdate
    ) -> DashboardDrillthroughResponse | None:
        rec = await session.get(DashboardDrillthroughRuleRecord, rule_id)
        if not rec or rec.source_dashboard_id != dashboard_id:
            return None
        for field, attr in [
            (body.source_widget_id, "source_widget_id"),
            (body.target_dashboard_id, "target_dashboard_id"),
            (body.trigger_column, "trigger_column"),
            (body.target_variable_name, "target_variable_name"),
            (body.label, "label"),
            (body.open_mode, "open_mode"),
        ]:
            if field is not None:
                setattr(rec, attr, field)
        await session.commit()
        await session.refresh(rec)
        return DashboardDrillthroughService._to_response(rec)

    @staticmethod
    async def delete_rule(session: AsyncSession, dashboard_id: str, rule_id: str) -> bool:
        rec = await session.get(DashboardDrillthroughRuleRecord, rule_id)
        if not rec or rec.source_dashboard_id != dashboard_id:
            return False
        await session.delete(rec)
        await session.commit()
        return True

    @staticmethod
    def build_drillthrough_url(
        target_dashboard_id: str, variable_name: str, value: str, base_path: str = "/dashboards/view"
    ) -> str:
        from urllib.parse import urlencode

        params: dict[str, str] = {"id": target_dashboard_id, variable_name: str(value)}
        return f"{base_path}?{urlencode(params)}"
