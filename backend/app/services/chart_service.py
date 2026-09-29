"""Chart data — delegates to chart engine registry."""

from app.models.schemas import ChartRequest, ChartResponse
from app.services.chart_engine.registry import build_chart, list_chart_types


class ChartService:
    @staticmethod
    def build_chart(dataset_id: str, req: ChartRequest) -> ChartResponse:
        return build_chart(dataset_id, req)

    @staticmethod
    def list_types() -> list[dict[str, str]]:
        return list_chart_types()
