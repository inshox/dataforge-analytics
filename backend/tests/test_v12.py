import pytest


@pytest.mark.asyncio
async def test_chart_types(client):
    r = await client.get("/api/v1/charts/types")
    assert r.status_code == 200
    types = {t["id"] for t in r.json()}
    assert "sankey" in types
    assert "funnel" in types
    assert "candlestick" in types


@pytest.mark.asyncio
async def test_sankey_chart(client, sample_csv):
    files = {"file": ("flow.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.post(
        f"/api/v1/datasets/{dataset_id}/charts",
        json={
            "chart_type": "funnel",
            "x_column": "region",
            "y_column": "revenue",
            "aggregation": "sum",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["chart_type"] == "funnel"
    assert len(body["data"]) >= 1


@pytest.mark.asyncio
async def test_forecast_holt_winters(client, sample_csv):
    files = {"file": ("ts.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.post(
        f"/api/v1/datasets/{dataset_id}/forecast",
        json={
            "date_column": "date",
            "value_column": "revenue",
            "horizon_days": 14,
            "method": "holt_winters",
            "confidence_level": 0.95,
        },
    )
    assert r.status_code == 200
    pts = r.json()["points"]
    assert any(p["is_forecast"] for p in pts)


@pytest.mark.asyncio
async def test_worker_submit(client, sample_csv):
    files = {"file": ("w.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]

    r = await client.post(
        "/api/v1/workers",
        json={"job_type": "import", "payload": {"dataset_id": dataset_id}},
    )
    assert r.status_code == 200
    assert r.json()["status"] in ("queued", "running", "completed")


@pytest.mark.asyncio
async def test_dashboard_templates(client):
    r = await client.get("/api/v1/dashboards/templates")
    assert r.status_code == 200
    assert len(r.json()) >= 4
