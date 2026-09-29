"""Lightweight SQLite migrations for v1.3+."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def run_migrations(engine: AsyncEngine) -> None:
    alters = [
        "ALTER TABLE dashboard_variables ADD COLUMN label VARCHAR(255) DEFAULT ''",
        "ALTER TABLE dashboard_variables ADD COLUMN column_name VARCHAR(255)",
        "ALTER TABLE dashboard_variables ADD COLUMN default_value_json TEXT DEFAULT 'null'",
        "ALTER TABLE dashboard_variables ADD COLUMN current_value_json TEXT DEFAULT 'null'",
        "ALTER TABLE dashboard_variables ADD COLUMN allowed_values_json TEXT DEFAULT '[]'",
        "ALTER TABLE dashboard_variables ADD COLUMN updated_at DATETIME",
        "ALTER TABLE dashboard_variables ADD COLUMN dataset_id VARCHAR(36)",
        "ALTER TABLE datasets ADD COLUMN import_stage VARCHAR(40)",
    ]
    async with engine.begin() as conn:
        for stmt in alters:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass
