"""Default local heuristic SQL provider (wraps existing analyst logic)."""

from typing import Any

from app.ai_providers.base import AIProvider, AIProviderKind, SQLGenerationResult
from app.models.schemas import ColumnInfo
from app.services.ai_analyst_service import AiAnalystService


class HeuristicAIProvider(AIProvider):
    kind = AIProviderKind.heuristic

    def is_available(self) -> bool:
        return True

    async def generate_sql(
        self,
        question: str,
        columns: list[dict[str, Any]],
        dataset_name: str,
    ) -> SQLGenerationResult:
        cols = [ColumnInfo(**c) if isinstance(c, dict) else c for c in columns]
        result = AiAnalystService.analyze("local", question, cols)
        return SQLGenerationResult(
            sql=result.sql,
            explanation=result.explanation,
            provider="heuristic",
        )
