"""Dataset relationship detection and management."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import DatasetRecord
from app.models.enterprise import DatasetRelationshipRecord
from app.models.schemas import RelationshipResponse, RelationshipSpec
from app.services.polars_utils import columns_from_json

KEY_PATTERNS = re.compile(
    r"(^id$|_id$|customer|product|order|invoice|user|account|sku|code$)",
    re.I,
)


class RelationshipService:
    @staticmethod
    async def list_relationships(session: AsyncSession) -> list[RelationshipResponse]:
        result = await session.execute(select(DatasetRelationshipRecord))
        return [RelationshipService._to_response(r) for r in result.scalars().all()]

    @staticmethod
    async def detect_relationships(session: AsyncSession) -> list[RelationshipResponse]:
        result = await session.execute(
            select(DatasetRecord).where(DatasetRecord.status == "ready")
        )
        datasets = result.scalars().all()
        found: list[RelationshipResponse] = []

        for i, left in enumerate(datasets):
            left_cols = {c.name for c in columns_from_json(left.columns_json)}
            for right in datasets[i + 1 :]:
                right_cols = {c.name for c in columns_from_json(right.columns_json)}
                for lc in left_cols:
                    if not KEY_PATTERNS.search(lc):
                        continue
                    for rc in right_cols:
                        if lc.lower() == rc.lower() or _columns_match(lc, rc):
                            spec = RelationshipSpec(
                                left_dataset_id=left.id,
                                right_dataset_id=right.id,
                                left_column=lc,
                                right_column=rc,
                                relationship_type="many_to_one",
                                confidence=0.85 if lc.lower() == rc.lower() else 0.7,
                                is_manual=False,
                            )
                            rec = await RelationshipService._upsert(session, spec)
                            found.append(rec)

        await session.commit()
        return found

    @staticmethod
    async def create_relationship(
        session: AsyncSession, body: RelationshipSpec
    ) -> RelationshipResponse:
        rec = await RelationshipService._upsert(session, body)
        await session.commit()
        return rec

    @staticmethod
    async def delete_relationship(session: AsyncSession, rel_id: str) -> bool:
        row = await session.get(DatasetRelationshipRecord, rel_id)
        if not row:
            return False
        await session.delete(row)
        await session.commit()
        return True

    @staticmethod
    async def graph(session: AsyncSession) -> dict:
        rels = await RelationshipService.list_relationships(session)
        nodes: dict[str, dict] = {}
        edges = []
        for r in rels:
            for ds_id in (r.left_dataset_id, r.right_dataset_id):
                if ds_id not in nodes:
                    rec = await session.get(DatasetRecord, ds_id)
                    nodes[ds_id] = {
                        "id": ds_id,
                        "label": rec.name if rec else ds_id,
                    }
            edges.append(
                {
                    "id": r.id,
                    "source": r.left_dataset_id,
                    "target": r.right_dataset_id,
                    "left_column": r.left_column,
                    "right_column": r.right_column,
                    "confidence": r.confidence,
                }
            )
        return {"nodes": list(nodes.values()), "edges": edges}

    @staticmethod
    async def _upsert(session: AsyncSession, body: RelationshipSpec) -> RelationshipResponse:
        existing = await session.execute(
            select(DatasetRelationshipRecord).where(
                DatasetRelationshipRecord.left_dataset_id == body.left_dataset_id,
                DatasetRelationshipRecord.right_dataset_id == body.right_dataset_id,
                DatasetRelationshipRecord.left_column == body.left_column,
                DatasetRelationshipRecord.right_column == body.right_column,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.confidence = body.confidence
            row.is_manual = 1 if body.is_manual else 0
        else:
            row = DatasetRelationshipRecord(
                id=str(uuid.uuid4()),
                left_dataset_id=body.left_dataset_id,
                right_dataset_id=body.right_dataset_id,
                left_column=body.left_column,
                right_column=body.right_column,
                relationship_type=body.relationship_type,
                confidence=body.confidence,
                is_manual=1 if body.is_manual else 0,
            )
            session.add(row)
        await session.flush()
        return RelationshipService._to_response(row)

    @staticmethod
    def _to_response(row: DatasetRelationshipRecord) -> RelationshipResponse:
        return RelationshipResponse(
            id=row.id,
            left_dataset_id=row.left_dataset_id,
            right_dataset_id=row.right_dataset_id,
            left_column=row.left_column,
            right_column=row.right_column,
            relationship_type=row.relationship_type,
            confidence=row.confidence,
            is_manual=bool(row.is_manual),
            created_at=row.created_at.isoformat() if row.created_at else None,
        )


def _columns_match(a: str, b: str) -> bool:
    a_norm = a.lower().replace("_", "")
    b_norm = b.lower().replace("_", "")
    return a_norm == b_norm or a_norm in b_norm or b_norm in a_norm
