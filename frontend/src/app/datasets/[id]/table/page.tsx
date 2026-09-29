"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useDatasetRoute } from "@/hooks/use-dataset-route";
import { useCallback, useMemo, useState } from "react";
import { Download, X, Eye, Save } from "lucide-react";
import { api, type SortSpec } from "@/lib/api";
import { EMPTY_FILTERS, EMPTY_SORT } from "@/lib/constants";
import { DatasetSubNav } from "@/components/layout/sidebar";
import { VirtualTable } from "@/components/data/virtual-table";
import { FilterBuilder } from "@/components/data/filter-builder";
import { FilterChips } from "@/components/data/filter-chips";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/app-store";
import { formatNumber } from "@/lib/utils";

const PAGE_SIZES = [50, 100, 250, 500, 1000];

export default function DatasetTablePage() {
  const { id, ready, isPlaceholder } = useDatasetRoute();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [viewName, setViewName] = useState("");

  const filters = useAppStore((s) => s.tableFilters[id] ?? EMPTY_FILTERS);
  const sort = useAppStore((s) => s.tableSort[id] ?? EMPTY_SORT);
  const globalSearch = useAppStore((s) => s.globalSearch[id] ?? "");
  const hidden = useAppStore((s) => s.hiddenColumns[id] ?? []);
  const columnWidths = useAppStore((s) => s.columnWidths[id] ?? {});

  const setFilters = useAppStore((s) => s.setTableFilters);
  const setSort = useAppStore((s) => s.setTableSort);
  const setGlobalSearch = useAppStore((s) => s.setGlobalSearch);
  const setHiddenColumns = useAppStore((s) => s.setHiddenColumns);
  const setColumnWidth = useAppStore((s) => s.setColumnWidth);

  const { data: dataset } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id),
    enabled: ready,
  });

  const { data: views = [], refetch: refetchViews } = useQuery({
    queryKey: ["views", id],
    queryFn: () => api.listViews(id),
    enabled: ready,
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["rows", id, page, pageSize, filters, sort, globalSearch],
    queryFn: () =>
      api.getRows(id, { page, page_size: pageSize, filters, sort, q: globalSearch || undefined }),
    enabled: ready && dataset?.status === "ready",
  });

  const allColumns = data?.columns.map((c) => c.name) ?? dataset?.columns.map((c) => c.name) ?? [];
  const visibleColumns = useMemo(
    () => allColumns.filter((c) => !hidden.includes(c)),
    [allColumns, hidden]
  );

  if (isPlaceholder) return null;

  const hasFilters = filters.length > 0 || globalSearch.length > 0;

  const onSort = useCallback(
    (column: string, multi: boolean) => {
      const existing = sort.find((s) => s.column === column);
      let next: SortSpec[];
      if (!existing) {
        next = multi ? [...sort, { column, descending: false }] : [{ column, descending: false }];
      } else if (!existing.descending) {
        next = sort.map((s) => (s.column === column ? { ...s, descending: true } : s));
      } else {
        next = sort.filter((s) => s.column !== column);
      }
      setSort(id, next);
      setPage(1);
    },
    [id, sort, setSort]
  );

  const toggleColumn = (col: string) => {
    if (hidden.includes(col)) {
      setHiddenColumns(id, hidden.filter((c) => c !== col));
    } else {
      setHiddenColumns(id, [...hidden, col]);
    }
  };

  const clearFilters = () => {
    setFilters(id, []);
    setGlobalSearch(id, "");
    setPage(1);
  };

  const saveView = async () => {
    const name = viewName.trim() || `View ${new Date().toLocaleString()}`;
    await api.saveView(id, { name, filters, sort, hidden_columns: hidden });
    setViewName("");
    void refetchViews();
    void queryClient.invalidateQueries({ queryKey: ["views", id] });
  };

  const loadView = (viewId: string) => {
    const v = views.find((x) => x.id === viewId);
    if (!v) return;
    setFilters(id, v.filters);
    setSort(id, v.sort);
    setHiddenColumns(id, v.hidden_columns);
    setPage(1);
  };

  const exportCsv = () => {
    window.open(
      api.exportCsvUrl(id, { filters, sort, q: globalSearch || undefined }),
      "_blank"
    );
  };

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-forge-text">{dataset?.name ?? "Table"}</h1>
        <div className="flex flex-wrap gap-2">
          {hasFilters && (
            <Button variant="ghost" onClick={clearFilters}>
              <X className="h-4 w-4" /> Clear filters
            </Button>
          )}
          <Button variant="secondary" onClick={exportCsv}>
            <Download className="h-4 w-4" /> Export CSV
          </Button>
        </div>
      </div>
      <DatasetSubNav datasetId={id} />

      <Card title="Global search" className="mb-4">
        <input
          className="w-full max-w-md rounded-lg border border-forge-border bg-forge-surface px-4 py-2 text-sm text-forge-text"
          placeholder="Search all columns…"
          value={globalSearch}
          onChange={(e) => {
            setGlobalSearch(id, e.target.value);
            setPage(1);
          }}
        />
      </Card>

      <Card title="Filters" className="mb-4">
        <FilterChips filters={filters} onChange={(f) => { setFilters(id, f); setPage(1); }} />
        <div className="mt-3">
          <FilterBuilder
            columns={allColumns}
            filters={filters}
            onChange={(f) => {
              setFilters(id, f);
              setPage(1);
            }}
          />
        </div>
      </Card>

      <Card title="Columns & saved views" className="mb-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {allColumns.map((col) => (
            <button
              key={col}
              type="button"
              className={`rounded-full border px-2 py-1 text-xs ${
                hidden.includes(col)
                  ? "border-forge-border text-forge-muted"
                  : "border-forge-text/30 bg-forge-accent-soft text-forge-text"
              }`}
              onClick={() => toggleColumn(col)}
            >
              <Eye className="mr-1 inline h-3 w-3" />
              {col}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-end gap-2 border-t border-forge-border pt-3">
          <input
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm text-forge-text"
            placeholder="View name"
            value={viewName}
            onChange={(e) => setViewName(e.target.value)}
          />
          <Button variant="secondary" onClick={() => void saveView()}>
            <Save className="h-4 w-4" /> Save view
          </Button>
          {views.length > 0 && (
            <select
              className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm text-forge-text"
              defaultValue=""
              onChange={(e) => e.target.value && loadView(e.target.value)}
            >
              <option value="">Load saved view…</option>
              {views.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </select>
          )}
        </div>
        <p className="mt-2 text-xs text-forge-muted">Shift+click column headers for multi-column sort.</p>
      </Card>

      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 text-sm text-forge-muted">
        {data && (
          <span>
            Page {data.page} of {data.total_pages} · {formatNumber(data.total_rows)} matching rows
          </span>
        )}
        <label className="flex items-center gap-2 text-forge-text">
          Rows per page
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-2 py-1 text-sm"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
          >
            {PAGE_SIZES.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>

      <VirtualTable
        columns={visibleColumns}
        rows={data?.rows ?? []}
        sort={sort}
        onSort={onSort}
        loading={isLoading}
        columnWidths={columnWidths}
        onColumnResize={(col, w) => setColumnWidth(id, col, w)}
      />

      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </Button>
        <Button
          variant="secondary"
          disabled={!data || page >= data.total_pages}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
        <Button variant="ghost" onClick={() => refetch()}>
          Refresh
        </Button>
      </div>
    </div>
  );
}
