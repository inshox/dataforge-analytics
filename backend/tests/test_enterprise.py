import pytest


@pytest.mark.asyncio
async def test_dashboard_crud(client):
    r = await client.post("/api/v1/dashboards", json={"name": "Sales KPIs"})
    assert r.status_code == 200
    dash = r.json()
    dash_id = dash["id"]

    r2 = await client.put(
        f"/api/v1/dashboards/{dash_id}",
        json={
            "widgets": [
                {
                    "widget_type": "kpi",
                    "dataset_id": "00000000-0000-4000-8000-000000000001",
                    "x": 0,
                    "y": 0,
                    "w": 4,
                    "h": 2,
                    "settings": {"label": "Rows", "metric": "count"},
                }
            ]
        },
    )
    assert r2.status_code == 200
    assert len(r2.json()["widgets"]) == 1

    dup = await client.post(f"/api/v1/dashboards/{dash_id}/duplicate")
    assert dup.status_code == 200

    await client.delete(f"/api/v1/dashboards/{dash_id}")
    await client.delete(f"/api/v1/dashboards/{dup.json()['id']}")


@pytest.mark.asyncio
async def test_insights(client, sample_csv):
    files = {"file": ("demo.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.post(f"/api/v1/datasets/{dataset_id}/insights")
    assert r.status_code == 200
    data = r.json()
    assert data["insights"]
    assert data["dataset_id"] == dataset_id


@pytest.mark.asyncio
async def test_sql_studio_saved(client, sample_csv):
    files = {"file": ("demo.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    save = await client.post(
        "/api/v1/sql-studio/saved",
        json={"name": "count all", "dataset_id": dataset_id, "sql_text": "SELECT COUNT(*) FROM dataset"},
    )
    assert save.status_code == 200

    listed = await client.get("/api/v1/sql-studio/saved")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1
