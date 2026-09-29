"use client";

import { useQuery } from "@tanstack/react-query";
import { RotateCcw, Save } from "lucide-react";
import { api } from "@/lib/api";
import { useDashboardFilters } from "@/contexts/dashboard-filter-context";
import { Button } from "@/components/ui/button";

export function DashboardFilterBar({ compact }: { compact?: boolean }) {
  const {
    variables,
    values,
    setVariable,
    resetFilters,
    saveDefaults,
    saveFilterPreset,
    loadFilterPreset,
    filterPresets,
  } = useDashboardFilters();

  if (!variables.length) return null;

  return (
    <div
      className={`mb-4 rounded-xl border border-forge-border bg-forge-surface p-3 ${compact ? "text-xs" : ""}`}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-forge-text">Dashboard filters</p>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={resetFilters}>
            <RotateCcw className="h-3.5 w-3.5" /> Reset
          </Button>
          <Button variant="secondary" onClick={() => void saveDefaults()}>
            <Save className="h-3.5 w-3.5" /> Save defaults
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              const name = window.prompt("Preset name");
              if (name) void saveFilterPreset(name);
            }}
          >
            Save preset
          </Button>
          {filterPresets.length > 0 && (
            <select
              className="rounded-lg border border-forge-border bg-forge-surface px-2 py-1.5 text-xs text-forge-text"
              defaultValue=""
              onChange={(e) => {
                if (e.target.value) loadFilterPreset(e.target.value);
                e.target.value = "";
              }}
            >
              <option value="">Load preset…</option>
              {filterPresets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>
      <div className={`grid gap-3 ${compact ? "grid-cols-1 sm:grid-cols-2" : "md:grid-cols-2 lg:grid-cols-3"}`}>
        {variables.map((v) => (
          <VariableControl key={v.id} variable={v} value={values[v.name]} onChange={setVariable} />
        ))}
      </div>
    </div>
  );
}

function VariableControl({
  variable: v,
  value,
  onChange,
}: {
  variable: { id: string; name: string; label: string; type: string; column_name?: string | null };
  value: unknown;
  onChange: (name: string, value: unknown) => void;
}) {
  if (v.type === "date_range") {
    const dr = (value as { from?: string; to?: string }) || {};
    return (
      <label className="block text-xs">
        <span className="text-forge-muted">{v.label}</span>
        <div className="mt-1 flex gap-2">
          <input
            type="date"
            className="w-full rounded border border-forge-border bg-forge-hover px-2 py-1 text-forge-text"
            value={dr.from ?? ""}
            onChange={(e) => onChange(v.name, { ...dr, from: e.target.value })}
          />
          <input
            type="date"
            className="w-full rounded border border-forge-border bg-forge-hover px-2 py-1 text-forge-text"
            value={dr.to ?? ""}
            onChange={(e) => onChange(v.name, { ...dr, to: e.target.value })}
          />
        </div>
      </label>
    );
  }

  if (v.type === "boolean") {
    return (
      <label className="flex items-center gap-2 text-xs text-forge-text">
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(v.name, e.target.checked)}
        />
        {v.label}
      </label>
    );
  }

  if (v.type === "select" || v.type === "multi_select") {
    return (
      <DistinctSelect
        label={v.label}
        name={v.name}
        column={v.column_name || v.name}
        datasetId={(v as { dataset_id?: string }).dataset_id}
        value={value}
        multi={v.type === "multi_select"}
        onChange={onChange}
      />
    );
  }

  return (
    <label className="block text-xs">
      <span className="text-forge-muted">{v.label}</span>
      <input
        className="mt-1 w-full rounded border border-forge-border bg-forge-hover px-2 py-1 text-forge-text"
        value={String(value ?? "")}
        onChange={(e) => onChange(v.name, e.target.value)}
      />
    </label>
  );
}

function DistinctSelect({
  label,
  name,
  column,
  datasetId,
  value,
  multi,
  onChange,
}: {
  label: string;
  name: string;
  column: string;
  datasetId?: string | null;
  value: unknown;
  multi?: boolean;
  onChange: (name: string, value: unknown) => void;
}) {
  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });
  const ds =
    datasets.find((d) => d.id === datasetId && d.status === "ready") ??
    datasets.find((d) => d.status === "ready");

  const { data, isLoading } = useQuery({
    queryKey: ["distinct", ds?.id, column],
    queryFn: () => api.distinctColumnValues(ds!.id, column),
    enabled: !!ds?.id && !!column,
  });

  const options = data?.values ?? [];

  if (!ds) {
    return (
      <label className="block text-xs">
        <span className="text-forge-muted">{label}</span>
        <p className="mt-1 text-forge-muted">No dataset for this variable.</p>
      </label>
    );
  }

  if (multi) {
    const selected = Array.isArray(value) ? value : [];
    return (
      <label className="block text-xs">
        <span className="text-forge-muted">{label}</span>
        <select
          disabled={isLoading}
          multiple
          className="mt-1 h-20 w-full rounded border border-forge-border bg-forge-hover px-2 py-1 text-forge-text"
          value={selected.map(String)}
          onChange={(e) => {
            const vals = Array.from(e.target.selectedOptions).map((o) => o.value);
            onChange(name, vals);
          }}
        >
          {options.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <label className="block text-xs">
      <span className="text-forge-muted">{label}</span>
      <select
        disabled={isLoading}
        className="mt-1 w-full rounded border border-forge-border bg-forge-hover px-2 py-1 text-forge-text"
        value={String(value ?? "")}
        onChange={(e) => onChange(name, e.target.value)}
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}
