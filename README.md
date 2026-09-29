# DataForge Analytics

**Local-first Power BI killer** — ultra-fast desktop analytics for Windows (`.exe`) and macOS (`.dmg`), with a premium web UI. Handle **50M+ rows** via Polars + DuckDB, server-side pagination, drag-and-drop dashboards, cross-filtering, drill-through, forecasting, and a local AI analyst — **100% offline-capable**.

> Standalone project (not CrowdAmp). Path: `C:\Users\SEBAS\Projects\DataForgeAnalytics`  
> Full capability map: **[PLATFORM.md](./PLATFORM.md)**

## Highlights

| Area | What you get |
|------|----------------|
| **Data** | Streaming CSV/Parquet/JSON import, virtual tables, DuckDB aggregates |
| **Dashboards** | 12-col grid, variables, global filters, click-to-filter, drill-through URLs |
| **Charts** | Plugin engine: sankey, funnel, candlestick, treemap, waterfall, … |
| **Forecast** | Holt-Winters, ARIMA, Prophet, linear/exponential + CSV export |
| **Workers** | Background import/forecast with cancel, retry, progress |
| **UX** | 5 themes, command palette (Ctrl+K), workspace tabs, presentation mode |
| **AI** | NL → SQL analyst, insights, anomalies, profiling (all local) |

**Oddzielna aplikacja** do analizy dużych zbiorów danych — lokalnie i jako desktop (Windows `.exe`, macOS `.dmg`). Zastępuje Excel przy pracy z milionami wierszy dzięki **Polars**, **DuckDB** i stronicowaniu po stronie serwera.

## Stack

| Warstwa | Technologia |
|---------|-------------|
| UI | Next.js 14, TypeScript, Tailwind CSS |
| Wykresy | Recharts |
| API | Python 3.11+, FastAPI |
| Dane | Polars, Parquet (cache), DuckDB (SQL Lab) |
| Metadane | SQLite (lokalnie) |
| Desktop | Tauri 2 |

## Funkcje (v1.4 Premium)

- **Widget editor** — Data, Style, Filters, Drill-through, Interactions, Export tabs; duplicate, lock, hide
- **Forecast & anomaly widgets** on dashboards with global filter support + forecast CSV export
- **Filter presets** — save/load named filter sets per dashboard
- **Per-variable dataset** for distinct dropdown values (correct column sourcing)
- **Drill breadcrumbs** + back navigation + “Drill available” chart badge
- **Transform Studio** (`/transform`) — preview Polars pipelines before apply
- **Import stages** — reading → validating → converting → profiling → indexing → complete
- **AI Analyst Pro** — executive summary, data quality notes, layout suggestions (local)

See [CHANGELOG.md](./CHANGELOG.md), [V14_PLAN.md](./V14_PLAN.md), and the **[v1.5 roadmap](./V15_ROADMAP.md)**.

## Funkcje (v1.3 — Dashboard variables & drill-through)

- **Dashboard variables** — region, date range, segment, etc. (server-side filters)
- **Global filter bar** — reset, save defaults, URL + localStorage persistence
- **Cross-widget filtering** — click a chart bar/slice to filter the whole dashboard
- **Drill-through** — navigate to detail dashboards with filters in the URL
- Demo dashboards: Executive Overview → Regional / Customer detail

Example URL:

`/dashboards/view?id=00000000-0000-4000-8000-000000000002&region=North&date_range_from=2024-01-05&date_range_to=2024-01-20`

## Funkcje (v1.1 Premium)

- Import CSV / XLSX / Parquet / JSON z podglądem, walidacją i **paskiem postępu** (tło + polling)
- Tabela z **wirtualnym scrollem** + stronicowanie po stronie serwera (Polars lazy, do 5M+ wierszy)
- Szybkie **agregacje DuckDB** (`POST /datasets/{id}/aggregate`)
- **Dashboard Builder** — siatka 12 kolumn, drag & drop, resize, eksport PDF/PNG
- **Chart Studio** — szablony wykresów, eksport PNG/SVG
- **SQL Studio** — Monaco, historia, zapisane zapytania, podgląd wykresu
- **AI Insights**, prognozy, wykrywanie anomalii (100% lokalnie)
- Relacje między datasetami, raporty HTML/PDF
- Desktop Tauri (Windows `.exe`, macOS `.dmg`)

## Struktura

```
DataForgeAnalytics/
├── backend/          # FastAPI + Polars + DuckDB
├── frontend/         # Next.js + Tauri (src-tauri/)
├── scripts/          # dev, przykładowe dane
├── ARCHITECTURE.md
└── README.md
```

## Wymagania

- **Node.js** 18+
- **Python** 3.12 (zalecane; `py -3.12` na Windows — unikaj 3.14, brak wheeli dla DuckDB)
- **Rust** (dla Tauri) — [rustup.rs](https://rustup.rs)
- Windows: Visual Studio Build Tools (linker MSVC)
- macOS: Xcode Command Line Tools

## Szybki start (web / dev)

### 1. Backend

```powershell
cd C:\Users\SEBAS\Projects\DataForgeAnalytics\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Dane lokalne trafiają do `backend/data/` (SQLite + Parquet).

### 2. Frontend

```powershell
cd C:\Users\SEBAS\Projects\DataForgeAnalytics\frontend
npm install
npm run dev
```

Otwórz [http://localhost:3000](http://localhost:3000). API: `http://127.0.0.1:8000`.

### 3. Przykładowy CSV

```powershell
# Po uruchomieniu UI: Datasets → Import → wybierz:
scripts\sample_sales.csv
```

## Dataset demo

Przy **pierwszym starcie** backendu (pusta baza) automatycznie importuje `Demo — Sales Sample` (16 wierszy). Na dashboardzie pojawi się karta **Otwórz demo**.

Wyłączenie: `SEED_DEMO_ON_STARTUP=false` w `backend/.env`.

## Desktop (Tauri)

Szczegóły buildu instalatora: **[BUILD.md](./BUILD.md)**.

### Ikony (jednorazowo)

```powershell
cd frontend
npm run tauri icon ..\public\icon.svg
```

(lub własny PNG 1024×1024)

### Dev z natywnym oknem

```powershell
cd frontend
npm run tauri:dev
```

Tauri uruchamia Next.js i **automatycznie startuje** backend Python na `127.0.0.1:8000`. Dane desktop: `%APPDATA%\DataForge Analytics\` (Windows) lub `~/Library/Application Support/DataForge Analytics/` (macOS).

### Build produkcyjny

```powershell
cd frontend
npm run tauri:build
```

| Platforma | Artefakt |
|-----------|----------|
| Windows | `frontend\src-tauri\target\release\bundle\nsis\*.exe` |
| macOS | `frontend\src-tauri\target\release\bundle\dmg\*.dmg` |

> Build macOS wymaga maszyny z macOS. Na Windows budujesz tylko `.exe`.

## Zmienne środowiskowe

| Zmienna | Opis |
|---------|------|
| `DATAFORGE_DATA_DIR` | Katalog danych (Parquet, SQLite, uploady) |
| `DATABASE_URL` | SQLite async URL (ustawiane przez Tauri) |
| `NEXT_PUBLIC_API_URL` | URL API dla frontendu (domyślnie `http://127.0.0.1:8000/api/v1`) |

## Trasy UI

- `/dashboard` — przegląd
- `/dashboards` — lista dashboardów; `/dashboards/view?id=` — edytor (Tauri)
- `/datasets` — lista i import
- `/datasets/view?id=` — dataset (overview, table, AI, charts, SQL)
- `/chart-studio` — studio wykresów
- `/sql` — globalne SQL Studio
- `/relationships` — graf relacji
- `/reports` — raporty
- `/settings` — motyw, API, reset danych

Skróty: **Ctrl+K** — paleta poleceń; **Ctrl+D** — datasets; **Ctrl+B** — dashboards.

## Docker (optional)

```powershell
docker compose up api
# API → http://127.0.0.1:8000
# Run frontend locally: cd frontend && npm run dev
```

Postgres/Redis: `docker compose --profile db up`. See [PLATFORM.md](./PLATFORM.md).

## Testy

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q

cd ..\frontend
npm run test
```

Obejmuje import, dashboard CRUD, variables/drill-through (v1.3), insights, SQL Studio, agregacje DuckDB i import w tle.

## Skrypt all-in-one (Windows)

```powershell
.\scripts\dev.ps1
```

Uruchamia backend i frontend w dwóch oknach.

## Licencja

MIT — użytek własny i komercyjny według potrzeb.
