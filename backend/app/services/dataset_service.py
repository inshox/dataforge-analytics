"""Dataset CRUD helpers."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import DatasetRecord, FilterPresetRecord, TableViewRecord
from app.models.schemas import DatasetSummary, FilterCondition, SortSpec, TableViewResponse
from app.services.polars_utils import columns_from_json


class DatasetService:
    @staticmethod
    def to_summary(record: DatasetRecord) -> DatasetSummary:
        tags = [t.strip() for t in (record.tags or "").split(",") if t.strip()]
        return DatasetSummary(
            id=record.id,
            name=record.name,
            description=record.description,
            tags=tags,
            source_filename=record.source_filename,
            source_format=record.source_format,
            file_size_bytes=record.file_size_bytes,
            row_count=record.row_count,
            column_count=record.column_count,
            columns=columns_from_json(record.columns_json),
            status=record.status,
            import_progress=record.import_progress,
            import_stage=record.import_stage,
            created_at=record.created_at.isoformat() if record.created_at else None,
        )

    @staticmethod
    async def list_datasets(session: AsyncSession, search: str | None = None) -> list[DatasetSummary]:
        q = select(DatasetRecord).order_by(DatasetRecord.created_at.desc())
        result = await session.execute(q)
        records = result.scalars().all()
        summaries = [DatasetService.to_summary(r) for r in records]
        if search:
            s = search.lower()
            summaries = [
                d
                for d in summaries
                if s in d.name.lower()
                or any(s in t.lower() for t in d.tags)
                or (d.source_filename and s in d.source_filename.lower())
            ]
        return summaries

    @staticmethod
    async def get_dataset(session: AsyncSession, dataset_id: str) -> DatasetRecord | None:
        return await session.get(DatasetRecord, dataset_id)

    @staticmethod
    async def save_filter_preset(
        session: AsyncSession, dataset_id: str, name: str, filters: list[FilterCondition]
    ) -> FilterPresetRecord:
        preset = FilterPresetRecord(
            dataset_id=dataset_id,
            name=name,
            filters_json=json.dumps([f.model_dump() for f in filters]),
        )
        session.add(preset)
        await session.commit()
        await session.refresh(preset)
        return preset

    @staticmethod
    async def list_table_views(session: AsyncSession, dataset_id: str) -> list[TableViewResponse]:
        result = await session.execute(
            select(TableViewRecord)
            .where(TableViewRecord.dataset_id == dataset_id)
            .order_by(TableViewRecord.created_at.desc())
        )
        views = []
        for v in result.scalars().all():
            views.append(
                TableViewResponse(
                    id=v.id,
                    name=v.name,
                    filters=[FilterCondition(**f) for f in json.loads(v.filters_json)],
                    sort=[SortSpec(**s) for s in json.loads(v.sort_json)],
                    hidden_columns=json.loads(v.hidden_columns_json),
                    created_at=v.created_at.isoformat() if v.created_at else None,
                )
            )
        return views

    @staticmethod
    async def save_table_view(
        session: AsyncSession,
        dataset_id: str,
        name: str,
        filters: list[FilterCondition],
        sort: list[SortSpec],
        hidden_columns: list[str],
    ) -> TableViewResponse:
        view = TableViewRecord(
            dataset_id=dataset_id,
            name=name,
            filters_json=json.dumps([f.model_dump() for f in filters]),
            sort_json=json.dumps([s.model_dump() for s in sort]),
            hidden_columns_json=json.dumps(hidden_columns),
        )
        session.add(view)
        await session.commit()
        await session.refresh(view)
        return TableViewResponse(
            id=view.id,
            name=view.name,
            filters=filters,
            sort=sort,
            hidden_columns=hidden_columns,
            created_at=view.created_at.isoformat() if view.created_at else None,
        )

    @staticmethod
    async def delete_table_view(session: AsyncSession, view_id: str) -> bool:
        view = await session.get(TableViewRecord, view_id)
        if not view:
            return False
        await session.delete(view)
        await session.commit()
        return True
