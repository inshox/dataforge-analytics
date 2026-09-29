"""Premium features: aggregate, background import, chart templates."""

import asyncio
import time

import pytest


@pytest.mark.asyncio
async def test_aggregate_duckdb(client, sample_csv):
    files = {"file": ("agg.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.post(
        f"/api/v1/datasets/{dataset_id}/aggregate",
        json={"group_by": ["region"], "aggregations": {"revenue": "sum"}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["rows"]
    assert "revenue_sum" in body["columns"] or any("revenue" in c for c in body["columns"])


@pytest.mark.asyncio
async def test_background_import(client, sample_csv):
    files = {"file": ("bg.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]

    r = await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize?background=true")
    assert r.status_code == 200
    assert r.json()["status"] in ("importing", "ready")

    for _ in range(40):
        ds = await client.get(f"/api/v1/datasets/{dataset_id}")
        if ds.json()["status"] == "ready":
            assert ds.json()["import_progress"] == 100
            return
        await asyncio.sleep(0.25)
    pytest.fail("Background import did not complete in time")


@pytest.mark.asyncio
async def test_chart_template_save(client):
    r = await client.post(
        "/api/v1/chart-studio/templates",
        json={
            "name": "Test template",
            "dataset_id": "00000000-0000-4000-8000-000000000001",
            "chart_type": "bar",
            "config": {"x_column": "region"},
        },
    )
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        listed = await client.get("/api/v1/chart-studio/templates")
        assert listed.status_code == 200


@pytest.mark.asyncio
async def test_demo_dashboard_list(client):
    listed = await client.get("/api/v1/dashboards")
    assert listed.status_code == 200
    names = [d["name"] for d in listed.json()]
    if any("Demo" in n for n in names):
        demo = next(d for d in listed.json() if "Demo" in d["name"])
        detail = await client.get(f"/api/v1/dashboards/{demo['id']}")
        assert detail.status_code == 200
        assert len(detail.json().get("widgets", [])) >= 1
