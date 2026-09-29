# Changelog

## 1.4.0 (2026)

### Added
- Full widget editor drawer (Data, Style, Filters, Drill-through, Interactions, Export)
- Forecast & anomaly dashboard widgets with global filter support
- Dashboard filter presets (save/load via API)
- Per-variable `dataset_id` for correct distinct dropdown values
- Drill breadcrumbs, back navigation, “Drill available” chart badge
- Transform Studio page + Polars pipeline preview API
- Import stages: reading → validating → converting → profiling → indexing → complete
- Forecast CSV export endpoint
- AI Analyst: executive summary, data quality notes, layout suggestions

### Tests
- `backend/tests/test_v14.py`
- Frontend Vitest drill-through URL tests

## 1.3.0

- Dashboard variables, cross-filter, drill-through, demo dashboards
