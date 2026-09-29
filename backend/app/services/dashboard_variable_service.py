"""Dashboard variables CRUD."""

from __future__ import annotations

import json
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    DashboardVariableCreate,
    DashboardVariableResponse,
    DashboardVariableUpdate,
)
from app.models.v12 import DashboardVariableRecord


def _loads(raw: str | None, fallback):
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


class DashboardVariableService:
    @staticmethod
    def _to_response(rec: DashboardVariableRecord) -> DashboardVariableResponse:
        current = _loads(rec.current_value_json, None)
        if current is None and rec.value_json:
            current = _loads(rec.value_json, None)
        return DashboardVariableResponse(
            id=rec.id,
            dashboard_id=rec.dashboard_id,
            name=rec.name,
            label=rec.label or rec.name,
            type=rec.var_type,
            column_name=rec.column_name,
            dataset_id=rec.dataset_id,
            default_value=_loads(rec.default_value_json, None),
            current_value=current,
            allowed_values=_loads(rec.allowed_values_json, []),
            created_at=rec.created_at.isoformat() if rec.created_at else None,
            updated_at=rec.updated_at.isoformat() if rec.updated_at else None,
        )

    @staticmethod
    async def list_variables(session: AsyncSession, dashboard_id: str) -> list[DashboardVariableResponse]:
        q = select(DashboardVariableRecord).where(DashboardVariableRecord.dashboard_id == dashboard_id)
        rows = (await session.execute(q)).scalars().all()
        return [DashboardVariableService._to_response(r) for r in rows]

    @staticmethod
    async def create_variable(
        session: AsyncSession, dashboard_id: str, body: DashboardVariableCreate
    ) -> DashboardVariableResponse:
        rec = DashboardVariableRecord(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            name=body.name,
            label=body.label or body.name,
            var_type=body.type,
            column_name=body.column_name,
            dataset_id=body.dataset_id,
            default_value_json=json.dumps(body.default_value),
            current_value_json=json.dumps(
                body.current_value if body.current_value is not None else body.default_value
            ),
            allowed_values_json=json.dumps(body.allowed_values),
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return DashboardVariableService._to_response(rec)

    @staticmethod
    async def update_variable(
        session: AsyncSession, dashboard_id: str, variable_id: str, body: DashboardVariableUpdate
    ) -> DashboardVariableResponse | None:
        rec = await session.get(DashboardVariableRecord, variable_id)
        if not rec or rec.dashboard_id != dashboard_id:
            return None
        if body.label is not None:
            rec.label = body.label
        if body.type is not None:
            rec.var_type = body.type
        if body.column_name is not None:
            rec.column_name = body.column_name
        if body.dataset_id is not None:
            rec.dataset_id = body.dataset_id
        if body.default_value is not None:
            rec.default_value_json = json.dumps(body.default_value)
        if body.current_value is not None:
            rec.current_value_json = json.dumps(body.current_value)
        if body.allowed_values is not None:
            rec.allowed_values_json = json.dumps(body.allowed_values)
        await session.commit()
        await session.refresh(rec)
        return DashboardVariableService._to_response(rec)

    @staticmethod
    async def delete_variable(session: AsyncSession, dashboard_id: str, variable_id: str) -> bool:
        rec = await session.get(DashboardVariableRecord, variable_id)
        if not rec or rec.dashboard_id != dashboard_id:
            return False
        await session.delete(rec)
        await session.commit()
        return True

    @staticmethod
    async def bulk_set_current(
        session: AsyncSession, dashboard_id: str, values: dict[str, object]
    ) -> list[DashboardVariableResponse]:
        variables = await DashboardVariableService.list_variables(session, dashboard_id)
        for var in variables:
            if var.name in values:
                await DashboardVariableService.update_variable(
                    session,
                    dashboard_id,
                    var.id,
                    DashboardVariableUpdate(current_value=values[var.name]),
                )
        return await DashboardVariableService.list_variables(session, dashboard_id)
