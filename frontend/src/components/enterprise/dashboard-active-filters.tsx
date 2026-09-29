"use client";

import { X } from "lucide-react";
import { useDashboardFilters } from "@/contexts/dashboard-filter-context";

export function DashboardActiveFilters() {
  const { variables, values, clearVariable } = useDashboardFilters();

  const active = variables.filter((v) => {
    const val = values[v.name];
    if (val === null || val === undefined || val === "") return false;
    if (Array.isArray(val) && val.length === 0) return false;
    if (v.type === "date_range" && typeof val === "object") {
      const dr = val as { from?: string; to?: string };
      return !dr.from && !dr.to ? false : true;
    }
    if (val === v.default_value) return false;
    return true;
  });

  if (!active.length) return null;

  return (
    <div className="mb-3 flex flex-wrap gap-2">
      {active.map((v) => (
        <span
          key={v.id}
          className="inline-flex items-center gap-1 rounded-full border border-forge-border bg-forge-hover px-2 py-0.5 text-xs text-forge-text"
        >
          {v.label}: {formatValue(values[v.name])}
          <button
            type="button"
            className="rounded p-0.5 hover:bg-forge-surface"
            onClick={() => clearVariable(v.name)}
            aria-label={`Clear ${v.label}`}
          >
            <X className="h-3 w-3" />
          </button>
        </span>
      ))}
    </div>
  );
}

function formatValue(val: unknown): string {
  if (Array.isArray(val)) return val.join(", ");
  if (typeof val === "object" && val !== null) {
    const dr = val as { from?: string; to?: string };
    return `${dr.from ?? "…"} → ${dr.to ?? "…"}`;
  }
  return String(val);
}
