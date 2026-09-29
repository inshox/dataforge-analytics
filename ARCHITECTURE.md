# DataForge Analytics — Architecture

> **Standalone project** — `C:\Users\SEBAS\Projects\DataForgeAnalytics` (not part of CrowdAmp).

## Overview

DataForge Analytics is a local-first, enterprise-grade data analysis platform that replaces Excel for large datasets. It combines a **Next.js** UI, a **Python/FastAPI** analytics engine (**Polars** + **DuckDB**), and **Tauri** for native Windows/macOS desktop distribution.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Tauri Shell (Rust)                          │
│  ┌──────────────────────┐    spawns on startup                 │
│  │  Next.js (static)    │◄──► localhost:8000                   │
│  │  React + Tailwind    │         FastAPI                      │
│  └──────────────────────┘              │                       │
└──────────────────────────────────────────┼──────────────────────┘
                                           ▼
                              ┌────────────────────────┐
                              │  Services Layer        │
                              │  Import / Query /      │
                              │  Analysis / Export     │
                              └───────────┬────────────┘
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │  Storage (local app data directory)     │
                    │  • SQLite — metadata, presets, tags     │
                    │  • Parquet — dataset bodies (chunked)   │
                    │  • DuckDB — in-process SQL over Parquet │
                    └─────────────────────────────────────────┘
```

## Monorepo Layout

```
dataforge/
├── backend/                 # FastAPI + Polars + DuckDB
│   └── app/
│       ├── api/routes/      # REST endpoints
│       ├── core/            # config, db, paths
│       ├── models/          # SQLAlchemy + Pydantic
│       └── services/        # business logic
├── frontend/                # Next.js App Router
│   └── src/
│       ├── app/             # routes (/dashboard, /datasets, …)
│       ├── components/      # UI primitives + features
│       └── lib/             # API client, types
├── src-tauri/               # Tauri v2 — desktop shell
├── scripts/                 # dev helpers, sample data
├── docker-compose.yml       # optional PostgreSQL + Redis
└── README.md
```

## Data Flow

### Import (CSV / XLSX / JSON / Parquet)

1. Client uploads file (multipart) or desktop picks file via dialog.
2. **ImportService** streams chunks → Polars `scan_csv` / readers with inferred schema.
3. Preview: first N rows returned without full materialization.
4. Full import: chunked write to **Parquet** under `{DATA_DIR}/datasets/{id}/data.parquet`.
5. Metadata row in SQLite: name, row_count, columns JSON, file_size, tags.

### Table view (virtualized UI)

1. Frontend requests `GET /datasets/{id}/rows?page=&page_size=&sort=&filters=`.
2. **QueryService** loads LazyFrame from Parquet, applies filters/sort, `slice` for page.
3. Never sends full dataset to browser.

### Analysis

- **AnalysisService** computes per-column stats via Polars expressions.
- Duplicates, nulls, outliers (IQR) run server-side.
- Group-by aggregations return small result sets.

### SQL Lab

- **SqlService** registers Parquet paths in DuckDB `CREATE VIEW dataset AS SELECT * FROM read_parquet(...)`.
- User SQL executed; results paginated like table view.

### Export

- Filtered LazyFrame → CSV/XLSX/JSON/Parquet stream.
- PDF report: ReportLab summary + embedded chart images (future chart snapshot).

## Performance Principles

| Concern | Approach |
|--------|----------|
| Memory | Polars LazyFrame, chunked CSV read, Parquet columnar storage |
| API payload | Pagination (default 100 rows), column projection optional |
| Heavy jobs | FastAPI `BackgroundTasks` + job status in SQLite (Celery optional via compose) |
| Frontend table | `@tanstack/react-virtual` virtual scroll |
| SQL | DuckDB zero-copy on Parquet where possible |

## Desktop vs Web

| Mode | Frontend | Backend | Data dir |
|------|----------|---------|----------|
| Dev web | `next dev` :3000 | `uvicorn` :8000 | `./data` |
| Tauri | static export in WebView | sidecar Python or bundled exe | OS app data dir |

Tauri `setup` hook spawns backend; `tauri.conf.json` bundles `backend` resources.

## Security (local app)

- Mock JWT auth middleware (optional `Authorization: Bearer demo`).
- CORS limited to `localhost` origins.
- No cloud dependency required.

## Route Map (Frontend)

| Path | Purpose |
|------|---------|
| `/dashboard` | Overview cards, recent datasets |
| `/datasets` | List, search, tags |
| `/datasets/[id]` | Dataset overview |
| `/datasets/[id]/table` | Virtualized grid + filters |
| `/datasets/[id]/analysis` | Column statistics |
| `/datasets/[id]/charts` | Chart builder |
| `/datasets/[id]/sql` | SQL Lab |
| `/reports` | PDF export history |
| `/settings` | Theme, data path, API URL |

## API Surface (v1)

Prefix: `/api/v1`

- `POST /datasets/import` — upload + preview/full
- `GET /datasets` — list
- `GET /datasets/{id}` — metadata
- `GET /datasets/{id}/rows` — paginated data
- `POST /datasets/{id}/filter` — apply filter preset
- `GET /datasets/{id}/stats` — column statistics
- `POST /datasets/{id}/aggregate` — group-by
- `POST /datasets/{id}/sql` — DuckDB query
- `GET /datasets/{id}/export` — download CSV/…
- `GET /health` — readiness

## Extension Points

- Swap SQLite → PostgreSQL via `DATABASE_URL`.
- Enable Celery workers in `docker-compose` for imports > N GB.
- Plugin chart types in `frontend/src/components/charts/`.
- Column type coercion UI → `PATCH /datasets/{id}/schema`.
