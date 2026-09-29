"""Dashboard filter presets — save/load variable value sets."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import DashboardFilterPresetCreate, DashboardFilterPresetResponse
from app.models.v12 import DashboardFilterPresetRecord


class DashboardFilterPresetService:
    @staticmethod
    def _to_response(rec: DashboardFilterPresetRecord) -> DashboardFilterPresetResponse:
        return DashboardFilterPresetResponse(
            id=rec.id,
            dashboard_id=rec.dashboard_id,
            name=rec.name,
            values=json.loads(rec.values_json or "{}"),
            created_at=rec.created_at.isoformat() if rec.created_at else None,
        )

    @staticmethod
    async def list_presets(
        session: AsyncSession, dashboard_id: str
    ) -> list[DashboardFilterPresetResponse]:
        q = select(DashboardFilterPresetRecord).where(
            DashboardFilterPresetRecord.dashboard_id == dashboard_id
        )
        rows = (await session.execute(q)).scalars().all()
        return [DashboardFilterPresetService._to_response(r) for r in rows]

    @staticmethod
    async def create_preset(
        session: AsyncSession, dashboard_id: str, body: DashboardFilterPresetCreate
    ) -> DashboardFilterPresetResponse:
        rec = DashboardFilterPresetRecord(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            name=body.name,
            values_json=json.dumps(body.values),
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return DashboardFilterPresetService._to_response(rec)

    @staticmethod
    async def delete_preset(session: AsyncSession, dashboard_id: str, preset_id: str) -> bool:
        q = delete(DashboardFilterPresetRecord).where(
            DashboardFilterPresetRecord.id == preset_id,
            DashboardFilterPresetRecord.dashboard_id == dashboard_id,
        )
        result = await session.execute(q)
        await session.commit()
        return result.rowcount > 0
