# DataForge Analytics v1.4 — Implementation Plan

## Scope (incremental on v1.3)

1. **Widget editor** — Full drawer: Data, Style, Filters, Drill-through, Interactions, Export; lock/hide/duplicate/rename.
2. **Dashboard filters** — `dataset_id` per variable; distinct from correct dataset; filter presets API + UI.
3. **Drill-through UX** — Breadcrumbs, back navigation, drill indicator on charts.
4. **Forecast/anomaly widgets** — Respect `extra_filters`; config in widget editor; CSV export.
5. **Chart engine** — Empty/error states; drill indicator; export hooks.
6. **Import polish** — Named stages (`reading` → `complete`); exposed on dataset API.
7. **Transform studio** — Pipeline preview/apply/save (Polars steps).
8. **AI Analyst Pro** — Executive summary, explain SQL, chart/layout hints (local heuristics).
9. **Reports** — Template list extended; forecast CSV endpoint.
10. **Tests & docs** — `test_v14.py`, Vitest; version 1.4.0.

## Deferred to v1.5

- Full dockable panel system
- PostgreSQL production mode
- Optional cloud LLM adapter implementation
- Android client
- Per-widget PDF export server-side
