# DataForge Analytics — v1.5 Roadmap

**Base:** v1.4.0 @ `C:\Users\SEBAS\Projects\DataForgeAnalytics`  
**Principle:** Extend incrementally. Do not break v1.4 tests (27 pytest + 5 Vitest). Run validation after each milestone.

**Validation commands (use after every milestone):**

```powershell
cd backend
.\.venv\Scripts\python -m pytest -q

cd ..\frontend
npm run test
npm run build

# Desktop (when touching Tauri / static export)
cd frontend
npm run tauri:build
```

---

## Phase 0 — Foundation (do first)

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 0.1 | Version bump & changelog | Set `1.5.0` in `backend/app/__version__.py`, `frontend/package.json`, `NEXT_PUBLIC_APP_VERSION`, `CHANGELOG.md` | `__version__.py`, `package.json`, `CHANGELOG.md` | — | Low | Keeps releases traceable |
| 0.2 | Roadmap test gate | Add `tests/test_v15_smoke.py` — health, demo dashboard IDs, transform preview | `backend/tests/test_v15_smoke.py` | 0.1 | Low | Fails fast if regressions |
| 0.3 | Shared types package | Align `FilterCondition`, `WidgetVariableFilter`, chart config types between `schemas.py` and `frontend/src/lib/api.ts` | `schemas.py`, `api.ts`, optional `frontend/src/lib/types/dashboard.ts` | — | Medium | Reduces editor/chart drift |

---

## 1. Widget Editor (Filters & Drill-through)

**Goal:** Production-grade widget configuration; no “settings only in JSON” gaps.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 1.1 | Split drawer into modules | Extract tabs: `widget-editor/data-tab.tsx`, `style-tab.tsx`, `filters-tab.tsx`, `drill-tab.tsx`, `interactions-tab.tsx`, `export-tab.tsx`; thin `widget-config-drawer.tsx` | `frontend/src/components/enterprise/widget-editor/*` | 0.3 | Medium | Easier Vitest per tab |
| 1.2 | Variable binding UX | Searchable variable list, operator help text, validation (column must exist on dataset), bind by variable **name** or **id** | `filters-tab.tsx`, `dashboard-filter-context.tsx` | 1.1 | Medium | Fix demo widgets using name in `variable_id` |
| 1.3 | Live filter preview | Debounced `filteredCount` + sample rows (new `POST .../filtered-preview` optional) | `filtered_count_service.py`, `datasets.py`, `filters-tab.tsx` | 1.2 | Medium | Server-side only; cap 100 rows |
| 1.4 | Drill rule editor v2 | Edit existing rules (PATCH), widget-scoped vs dashboard-scoped, parent dashboard name, test link “Open target” | `dashboard_drillthrough_service.py`, `dashboards.py`, `drill-tab.tsx` | 1.1 | Medium | Uses `PATCH .../drillthrough/{id}` (verify exists) |
| 1.5 | Interactions tab | Toggle: cross-filter vs drill-on-click; Ctrl+click = cross-filter only; double-click = drill | `interactions-tab.tsx`, `filtered-widget-body.tsx` | 1.4 | Medium | Power BI–like affordance |
| 1.6 | Export tab actions | Per-widget PNG/SVG from drawer (reuse `chart-export.ts`); copy widget JSON | `export-tab.tsx`, `chart-renderer.tsx` | 1.1 | Low | |
| 1.7 | Widget editor tests | Vitest: binding serialization, operator mapping, drill href | `widget-editor.test.ts`, `dashboard-filters.test.ts` | 1.2–1.6 | Medium | Target +8 frontend tests |

**Validate:** `npm run test`; manual: open widget ⚙ → each tab saves to `settings` and persists on dashboard Save.

---

## 2. Dashboard Grid & UX

**Goal:** Premium dashboard builder feel; lock/hide/present mode polished.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 2.1 | **Grid lock enforcement** | When `settings.locked`, set `static: true` on layout item; disable drag handle | `dashboard-grid.tsx`, `dashboard-editor.tsx` | — | Medium | v1.4 stores flag only |
| 2.2 | Hidden widget chrome | Show dashed placeholder in edit mode; fully hidden in presentation | `dashboard-editor.tsx`, `filtered-widget-body.tsx` | 2.1 | Low | |
| 2.3 | Variable manager panel | CRUD variables without API-only: name, type, dataset, column, defaults | `dashboard-variables-panel.tsx`, `dashboards.py` | 0.3 | Medium | Complements filter bar |
| 2.4 | Filter preset manager | List/delete/rename presets in UI | `dashboard-filter-bar.tsx`, `dashboard-filter-context.tsx` | — | Low | API exists in v1.4 |
| 2.5 | Drill breadcrumbs v2 | Dynamic trail from drill rules graph (not hardcoded demo IDs) | `dashboard-drill-breadcrumbs.tsx`, `dashboard_drillthrough_service.py` | 1.4 | Medium | Optional `parent_dashboard_id` on rules |
| 2.6 | Presentation mode polish | Hide editor chrome, full-bleed grid, keyboard Esc, URL `?present=1` | `dashboard-editor.tsx`, `dashboards/view/page.tsx` | 2.2 | Low | |
| 2.7 | Live refresh v2 | Configurable interval; pause when tab hidden; worker-friendly backoff | `dashboard-editor.tsx`, `filtered-widget-body.tsx` | — | Low | Avoid API storms |

**Validate:** `npm run build`; drag locked widget (should not move); presentation hides filters optionally (setting).

---

## 3. Chart Engine (audit & completion)

**Goal:** Every registered chart type: typed config, backend builder, renderer, export, click, empty/error.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 3.1 | Chart audit matrix | Document in `docs/CHART_MATRIX.md`: type × backend × frontend × export × click | `docs/CHART_MATRIX.md` | — | Low | Source of truth |
| 3.2 | Backend registry parity | Ensure `chart_engine/registry.py` + `builders.py` cover: gauge, radar, heatmap, boxplot, OHLC | `builders.py`, `chart_service.py`, `schemas.py` | 3.1 | High | DuckDB/Polars per type |
| 3.3 | Frontend registry parity | `registry.ts` + `chart-renderer.tsx` + `advanced/*`; no silent fallback to bar | `chart-renderer.tsx`, `advanced/*` | 3.2 | High | gauge/radar currently map to bar |
| 3.4 | Typed widget config | `ChartWidgetConfig` discriminated union per `chart_type` | `frontend/src/lib/charts/types.ts` | 0.3, 3.3 | Medium | Used in Data tab |
| 3.5 | Click interactions audit | Consistent `onDataPointClick` for heatmap, treemap, funnel, sankey nodes | `chart-renderer.tsx`, builders | 1.5 | Medium | |
| 3.6 | Export audit | PNG/SVG for all types; fix treemap/sankey container sizing | `chart-export.ts`, `chart-renderer.tsx` | 3.3 | Medium | |
| 3.7 | Chart tests | Vitest registry coverage; pytest one request per chart type on demo dataset | `registry.test.ts`, `tests/test_charts_v15.py` | 3.2–3.3 | Medium | +10–15 tests |

**Validate:** `pytest tests/test_charts_v15.py -q`; Chart Studio + dashboard widgets for each type.

---

## 4. Forecast & Anomaly Widgets

**Goal:** Parity with chart widgets; confidence, seasonality, export, table view.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 4.1 | Forecast config in Data tab | Horizon, method, confidence slider, seasonality, date/value columns | `widget-editor/data-tab.tsx`, `dashboard-forecast-widget.tsx` | 1.1 | Medium | |
| 4.2 | Forecast confidence bands | Render upper/lower in chart (Recharts Area) | `dashboard-forecast-widget.tsx`, `forecast_service.py` | 4.1 | Medium | Points already have lower/upper |
| 4.3 | Anomaly config | Methods checkboxes (iqr, zscore, rolling), max items | `dashboard-anomaly-widget.tsx`, `anomaly_service.py` | 1.1 | Low | Pass methods in body (v1.4 partial) |
| 4.4 | Anomaly table widget mode | Optional mini-table with severity chips | `dashboard-anomaly-widget.tsx` | 4.3 | Medium | |
| 4.5 | Filter edge cases | Empty state when filters exclude all rows; clear messaging | `dashboard-forecast-widget.tsx`, `dashboard-anomaly-widget.tsx` | 1.2 | Low | |
| 4.6 | Tests | pytest forecast+filters+csv; Vitest forecast widget renders loading | `test_v15_forecast.py`, `forecast-widget.test.tsx` | 4.1–4.3 | Medium | |

**Validate:** Executive demo dashboard with date_range filter → forecast updates.

---

## 5. Transform Studio (complete)

**Goal:** Power Query–like MVP: joins, split, merge, pipeline list, apply with undo.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 5.1 | Step library UI | Step picker: rename, cast, filter, dedupe, calc, split, merge, group_by, join | `frontend/src/app/transform/page.tsx`, `transform-step-builder.tsx` | — | High | |
| 5.2 | Backend step implementations | Implement missing ops in `transformation_service.py`: split, merge, join (Polars), calc expression (safe subset) | `transformation_service.py` | 5.1 | High | No arbitrary code exec |
| 5.3 | Pipeline list page | List/load/delete/run pipelines per dataset | `transforms.py`, `transform/page.tsx`, `api.ts` | v1.4 pipelines API | Medium | |
| 5.4 | Preview diff | Before/after column list + row count delta | `TransformPreviewResponse` extend | 5.2 | Medium | |
| 5.5 | Apply with backup | Copy parquet to `datasets/{id}/snapshots/{ts}.parquet` before run | `transformation_service.py`, `core/storage.py` | 5.2 | Medium | Local-first safety |
| 5.6 | Dataset picker from relationships | Suggest join keys from `relationship_service.py` | `relationships` UI link | 5.2 | Medium | |
| 5.7 | Tests | pytest each op; Vitest step builder serializes JSON | `tests/test_transform_v15.py` | 5.2–5.3 | Medium | |

**Validate:** Rename column preview → run pipeline → dataset table reflects change; pytest transform suite.

---

## 6. Worker UI (import & jobs)

**Goal:** Visible, controllable background work.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 6.1 | Import modal stages | Show `import_stage` + progress bar during finalize poll | `datasets` import UI, `dataset_service.py` | v1.4 stages | Medium | |
| 6.2 | Cancel import | Wire UI to existing cancel endpoint; disable finalize | `import_service.py`, import components | — | Low | Backend exists |
| 6.3 | Retry failed import | Reset status `error` → `preview` or re-queue job | `import_service.py`, `worker_service.py` | 6.1 | Medium | |
| 6.4 | Clear failed job | Delete dataset row + upload artifacts | `datasets.py`, Settings or Datasets list | 6.3 | Low | |
| 6.5 | Worker queue panel v2 | Filter by type, cancel job, retry, error detail expand | `settings/page.tsx`, `workers.py`, `worker_service.py` | — | Medium | |
| 6.6 | CPU/memory sparkline | Optional: poll `worker_stats` history (client buffer) | `settings/page.tsx`, `system_service.py` | 6.5 | Low | |
| 6.7 | Tests | pytest import stages transition; Vitest stage label mapping | `test_v15_import.py` | 6.1–6.3 | Medium | |

**Validate:** Import large CSV → stages animate; cancel mid-import; pytest pass.

---

## 7. Export & Reports

**Goal:** Shareable outputs for execs; per-widget and dashboard.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 7.1 | Per-widget PDF | Server route: render widget spec → HTML → PDF (reportlab/weasyprint) or client print | `export_service.py`, `dashboards.py` | 3.3 | High | Prefer server for Tauri consistency |
| 7.2 | Dashboard PDF v2 | Include filter state subtitle, timestamp, theme | `report_service.py`, `dashboards.py` export | — | Medium | v1.4 PDF exists |
| 7.3 | Report templates UI | executive, sales, finance, marketing — parameterize dataset + dashboards | `reports/page.tsx`, `report_service.py` | 7.2 | Medium | |
| 7.4 | Query export | CSV/Parquet from SQL studio result | `sql_studio_service.py`, `sql/page.tsx` | — | Medium | |
| 7.5 | Batch export zip | Multi-widget PNG zip from dashboard | new `dashboard_export_service.py` | 7.1 | Medium | |
| 7.6 | Tests | pytest PDF returns 200; Vitest export tab triggers download mock | `test_v15_export.py` | 7.1–7.2 | Medium | |

**Validate:** Export dashboard PDF; single widget PDF; file opens.

---

## 8. AI Analyst (local + optional cloud interface)

**Goal:** Keep local-first; add pluggable adapter without requiring cloud.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 8.1 | `LLMProvider` protocol | Python `Protocol`: `complete(prompt) -> str`; implementations: `HeuristicProvider`, `NoopProvider` | `backend/app/services/llm/` | — | Medium | No network in default |
| 8.2 | Settings: provider select | `local` / `openai_compatible` (URL + key in env only, never commit) | `settings/page.tsx`, `.env.example` | 8.1 | Medium | Security: key from env |
| 8.3 | Enhanced NL→SQL | Optional LLM pass post-heuristic; fallback on error | `ai_analyst_service.py` | 8.1 | High | |
| 8.4 | Explain results | After execute: summary of row count, top values | `datasets/[id]/analyst/page.tsx` | 8.1 | Medium | |
| 8.5 | Suggest dashboard layout | Return widget list JSON from analyst; “Apply template” button | `ai_analyst_service.py`, `dashboard-editor.tsx` | 8.4, 2.3 | High | |
| 8.6 | Tests | pytest heuristic path always works; mock LLM adapter | `test_v15_analyst.py` | 8.1 | Medium | |

**Validate:** Analyst works offline; with `LLM_PROVIDER=none`, identical to v1.4.

---

## 9. PostgreSQL production mode

**Goal:** Optional Postgres for metadata; SQLite remains default for desktop.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 9.1 | Async Postgres URL | Document `DATABASE_URL=postgresql+asyncpg://...`; verify SQLAlchemy models | `core/database.py`, `docker-compose.yml` | — | Medium | |
| 9.2 | Migration runner v2 | Idempotent migrations table; move ALTERs from `migrations.py` | `core/migrations.py` | 9.1 | High | |
| 9.3 | Connection pool settings | Pool size env vars for Docker | `core/config.py` | 9.1 | Low | |
| 9.4 | INSTALL.md | Desktop = SQLite; Server = Postgres guide | `INSTALL.md` | 9.1–9.3 | Low | |
| 9.5 | Tests | CI job matrix: sqlite + postgres (optional service) | `.github/workflows` or local docker | 9.2 | High | |

**Validate:** `docker compose --profile db up`; API starts with Postgres URL.

---

## 10. Vitest & pytest expansion

**Goal:** Confidence for refactors; target **40+ pytest**, **20+ Vitest**.

| # | Task | Description | Files / components | Depends on | Complexity | Notes |
|---|------|-------------|-------------------|------------|------------|-------|
| 10.1 | Frontend integration tests | RTL: filter bar, preset load, drill breadcrumb render | `frontend/src/**/*.test.tsx` | 2.x, 1.x | High | Mock `api.ts` |
| 10.2 | Chart registry snapshot | Each plugin id in registry test | `registry.test.ts` | 3.1 | Low | |
| 10.3 | E2E smoke (optional) | Playwright: open demo dashboard, change filter | `e2e/dashboard.spec.ts` | — | High | Bonus |
| 10.4 | CI script | `scripts/verify.ps1` runs pytest + vitest + build | `scripts/verify.ps1` | — | Low | |

**Validate:** `.\scripts\verify.ps1` green.

---

## Recommended execution order (sprints)

### Sprint 1 — High impact UX (2–3 weeks)
1. Phase 0  
2. **2.1** Grid lock  
3. **1.1–1.3** Widget editor filters polish  
4. **6.1–6.3** Worker/import UI  
5. **3.1–3.3** Chart audit + gauge/radar/heatmap fixes  

### Sprint 2 — Data power (2–3 weeks)
6. **5.1–5.5** Transform studio complete  
7. **4.1–4.4** Forecast/anomaly polish  
8. **7.1–7.3** Export PDF + reports  

### Sprint 3 — Production & quality (2 weeks)
9. **2.3–2.5** Variables + dynamic breadcrumbs  
10. **8.1–8.4** LLM adapter interface (local default)  
11. **9.1–9.4** Postgres mode docs + migrations  
12. **10.1–10.4** Test expansion  

---

## Bonus (optional, post–v1.5.0)

| Task | Description | Complexity |
|------|-------------|------------|
| B1 | Real-time collaboration (shared filter URL only — already partial) | Medium |
| B2 | Dataset encryption at rest (SQLCipher / file-level) | High |
| B3 | Incremental refresh / scheduled pipeline run (local cron) | High |
| B4 | Custom themes editor (CSS variables export) | Medium |
| B5 | Mobile-responsive dashboard view-only mode | Medium |
| B6 | Plugin SDK for third-party chart types | High |
| B7 | Advanced drill: right-click context menu | Low |
| B8 | Live refresh WebSocket (local SSE from FastAPI) | Medium |

---

## Risk register

| Risk | Mitigation |
|------|------------|
| Chart audit balloons scope | Fix P0 types first (bar/line/pie/KPI); tier-2 advanced charts next |
| Transform `join` memory on huge data | Polars lazy + limit preview; full run via worker job |
| PDF export native deps | Optional feature flag; HTML export fallback |
| Postgres migration drift | Single `schema_migrations` table; never edit old migrations |
| Breaking v1.4 tests | Run full pytest + vitest before each PR merge |

---

## Definition of done (v1.5.0)

- [ ] All Sprint 1–3 **required** tasks complete  
- [ ] `pytest -q` ≥ 40 tests, all pass  
- [ ] `npm run test` ≥ 20 tests, all pass  
- [ ] `npm run build` success  
- [ ] `npm run tauri:build` success on Windows  
- [ ] README + PLATFORM.md + CHANGELOG updated  
- [ ] No regression on demo dashboards (`000…002/003/004`)  
- [ ] Local-first default unchanged (no required cloud keys)  

---

## Quick reference — key paths

| Module | Path |
|--------|------|
| Widget editor | `frontend/src/components/enterprise/widget-config-drawer.tsx` |
| Dashboard | `frontend/src/components/enterprise/dashboard-editor.tsx` |
| Charts | `frontend/src/components/charts/chart-renderer.tsx`, `backend/app/services/chart_engine/` |
| Transform | `backend/app/services/transformation_service.py`, `frontend/src/app/transform/page.tsx` |
| Workers | `backend/app/services/worker_service.py`, `frontend/src/app/settings/page.tsx` |
| Variables | `backend/app/services/dashboard_variable_service.py`, `dashboard-filter-context.tsx` |
| Tests | `backend/tests/`, `frontend/src/lib/*.test.ts` |
