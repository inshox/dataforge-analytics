"""Chart Studio templates."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enterprise import ChartTemplateRecord
from app.models.schemas import ChartTemplateCreate, ChartTemplateResponse


class ChartTemplateService:
    @staticmethod
    async def list_templates(session: AsyncSession, dataset_id: str | None = None) -> list[ChartTemplateResponse]:
        q = select(ChartTemplateRecord).order_by(ChartTemplateRecord.created_at.desc())
        if dataset_id:
            q = q.where(ChartTemplateRecord.dataset_id == dataset_id)
        result = await session.execute(q)
        return [ChartTemplateService._to_response(r) for r in result.scalars().all()]

    @staticmethod
    async def create_template(session: AsyncSession, body: ChartTemplateCreate) -> ChartTemplateResponse:
        rec = ChartTemplateRecord(
            id=str(uuid.uuid4()),
            name=body.name,
            dataset_id=body.dataset_id,
            chart_type=body.chart_type,
            config_json=json.dumps(body.config),
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return ChartTemplateService._to_response(rec)

    @staticmethod
    async def delete_template(session: AsyncSession, template_id: str) -> bool:
        rec = await session.get(ChartTemplateRecord, template_id)
        if not rec:
            return False
        await session.delete(rec)
        await session.commit()
        return True

    @staticmethod
    def _to_response(r: ChartTemplateRecord) -> ChartTemplateResponse:
        return ChartTemplateResponse(
            id=r.id,
            name=r.name,
            dataset_id=r.dataset_id,
            chart_type=r.chart_type,
            config=json.loads(r.config_json),
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
