import json

import pytest


@pytest.mark.asyncio
async def test_health_root(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"]
    assert data["database"] in ("ok", "error")
    assert data["duckdb"] == "ok"
    assert data["polars"] == "ok"
    assert "data_directory" in data


@pytest.mark.asyncio
async def test_health_api_prefix(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_import_preview_and_finalize(client, sample_csv):
    files = {"file": ("demo.csv", sample_csv, "text/csv")}
    r = await client.post("/api/v1/datasets/import/preview", files=files)
    assert r.status_code == 200
    preview = r.json()
    assert preview["dataset_id"]
    assert len(preview["columns"]) > 0
    assert preview["detected_separator"]

    dataset_id = preview["dataset_id"]
    r2 = await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_rows_pagination(client, sample_csv):
    files = {"file": ("demo.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.get(f"/api/v1/datasets/{dataset_id}/rows?page=1&page_size=5")
    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["rows"]) <= 5
    assert data["total_rows"] >= len(data["rows"])


@pytest.mark.asyncio
async def test_stats(client, sample_csv):
    files = {"file": ("demo.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.get(f"/api/v1/datasets/{dataset_id}/stats")
    assert r.status_code == 200
    stats = r.json()
    assert stats["row_count"] > 0
    assert len(stats["columns"]) > 0


@pytest.mark.asyncio
async def test_sql_lab(client, sample_csv):
    files = {"file": ("demo.csv", sample_csv, "text/csv")}
    preview = (await client.post("/api/v1/datasets/import/preview", files=files)).json()
    dataset_id = preview["dataset_id"]
    await client.post(f"/api/v1/datasets/{dataset_id}/import/finalize")

    r = await client.post(
        f"/api/v1/datasets/{dataset_id}/sql",
        json={"query": "SELECT * FROM dataset LIMIT 3", "page": 1, "page_size": 10},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["rows"]) <= 3


@pytest.mark.asyncio
async def test_csv_validation_empty(client):
    files = {"file": ("empty.csv", b"", "text/csv")}
    r = await client.post("/api/v1/datasets/import/preview", files=files)
    assert r.status_code == 400
    body = r.json()
    assert body.get("error") is True or "detail" in body
