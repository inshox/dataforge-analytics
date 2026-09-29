import pytest

from app.services.dashboard_drillthrough_service import DashboardDrillthroughService


@pytest.mark.asyncio
async def test_variable_crud(client, sample_csv):
    files = {"file": ("v13.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    dash = (await client.post("/api/v1/dashboards", json={"name": "Filter Test"})).json()
    dash_id = dash["id"]

    created = await client.post(
        f"/api/v1/dashboards/{dash_id}/variables",
        json={
            "name": "region",
            "label": "Region",
            "type": "select",
            "column_name": "region",
            "default_value": "North",
            "current_value": "North",
        },
    )
    assert created.status_code == 200
    var_id = created.json()["id"]

    listed = await client.get(f"/api/v1/dashboards/{dash_id}/variables")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patched = await client.patch(
        f"/api/v1/dashboards/{dash_id}/variables/{var_id}",
        json={"current_value": "South"},
    )
    assert patched.status_code == 200
    assert patched.json()["current_value"] == "South"

    distinct = await client.get(f"/api/v1/datasets/{dataset_id}/columns/region/distinct")
    assert distinct.status_code == 200
    assert "North" in distinct.json()["values"]

    count = await client.post(
        f"/api/v1/datasets/{dataset_id}/filtered-count",
        json={
            "extra_filters": [
                {"column": "region", "operator": "equals", "value": "North"}
            ]
        },
    )
    assert count.status_code == 200
    assert count.json()["total_rows"] >= 1

    chart = await client.post(
        f"/api/v1/datasets/{dataset_id}/charts",
        json={
            "chart_type": "bar",
            "x_column": "region",
            "y_column": "revenue",
            "aggregation": "sum",
            "extra_filters": [
                {"column": "region", "operator": "equals", "value": "North"}
            ],
        },
    )
    assert chart.status_code == 200

    await client.delete(f"/api/v1/dashboards/{dash_id}/variables/{var_id}")
    await client.delete(f"/api/v1/dashboards/{dash_id}")


@pytest.mark.asyncio
async def test_drillthrough_rule(client):
    dash_a = (await client.post("/api/v1/dashboards", json={"name": "A"})).json()
    dash_b = (await client.post("/api/v1/dashboards", json={"name": "B"})).json()
    r = await client.post(
        f"/api/v1/dashboards/{dash_a['id']}/drillthrough",
        json={
            "target_dashboard_id": dash_b["id"],
            "trigger_column": "region",
            "target_variable_name": "region",
            "label": "Go to B",
        },
    )
    assert r.status_code == 200
    url = DashboardDrillthroughService.build_drillthrough_url(
        dash_b["id"], "region", "Europe"
    )
    assert "id=" in url
    assert "region=Europe" in url.replace("%20", " ")


def test_drillthrough_url_encoding():
    url = DashboardDrillthroughService.build_drillthrough_url(
        "abc-123", "region", "North America"
    )
    assert "abc-123" in url
