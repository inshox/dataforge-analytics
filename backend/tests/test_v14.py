"""v1.4 — filter presets, transforms, forecast filters, variable dataset_id."""

import pytest

from app.services.dashboard_drillthrough_service import DashboardDrillthroughService
from app.services.transformation_service import TransformationService
from app.models.schemas import TransformPreviewRequest, TransformStep


async def _ready_dataset(client, sample_csv) -> str:
    files = {"file": ("v14.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")
    return dataset_id


@pytest.mark.asyncio
async def test_variable_with_dataset_id(client, sample_csv):
    dataset_id = await _ready_dataset(client, sample_csv)
    dash = await client.post(
        "/api/v1/dashboards",
        json={"name": "v14 vars", "description": "test"},
    )
    assert dash.status_code == 200
    dash_id = dash.json()["id"]
    var = await client.post(
        f"/api/v1/dashboards/{dash_id}/variables",
        json={
            "name": "region",
            "label": "Region",
            "type": "select",
            "column_name": "region",
            "dataset_id": dataset_id,
            "default_value": "North",
        },
    )
    assert var.status_code == 200
    assert var.json()["dataset_id"] == dataset_id


@pytest.mark.asyncio
async def test_filter_preset_crud(client, sample_csv):
    await _ready_dataset(client, sample_csv)
    dash = await client.post("/api/v1/dashboards", json={"name": "v14 presets"})
    dash_id = dash.json()["id"]
    created = await client.post(
        f"/api/v1/dashboards/{dash_id}/filter-presets",
        json={"name": "Q1", "values": {"region": "North"}},
    )
    assert created.status_code == 200
    listed = await client.get(f"/api/v1/dashboards/{dash_id}/filter-presets")
    assert len(listed.json()) >= 1
    preset_id = created.json()["id"]
    deleted = await client.delete(f"/api/v1/dashboards/{dash_id}/filter-presets/{preset_id}")
    assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_transform_preview(client, sample_csv):
    dataset_id = await _ready_dataset(client, sample_csv)
    body = TransformPreviewRequest(
        steps=[TransformStep(op="select_columns", params={"columns": ["region", "revenue"]})],
        limit=5,
    )
    res = TransformationService.preview(dataset_id, body)
    assert res.row_count >= 0
    assert any(c.name == "region" for c in res.columns)


@pytest.mark.asyncio
async def test_forecast_with_extra_filters(client, sample_csv):
    dataset_id = await _ready_dataset(client, sample_csv)
    res = await client.post(
        f"/api/v1/datasets/{dataset_id}/forecast",
        json={
            "date_column": "date",
            "value_column": "revenue",
            "horizon_days": 7,
            "method": "linear",
            "extra_filters": [
                {"column": "region", "operator": "equals", "value": "North"},
            ],
        },
    )
    assert res.status_code == 200
    assert len(res.json()["points"]) > 0


def test_drillthrough_url_v14():
    url = DashboardDrillthroughService.build_drillthrough_url(
        "target-id", "region", "Europe"
    )
    assert "id=target-id" in url
    assert "region=Europe" in url
