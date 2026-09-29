"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X, Plus, Trash2 } from "lucide-react";
import {
  api,
  type DashboardDrillthroughRule,
  type DashboardWidget,
  type WidgetVariableFilter,
} from "@/lib/api";
import { useDashboardFilters } from "@/contexts/dashboard-filter-context";
import { Button } from "@/components/ui/button";

const OPERATORS = ["eq", "neq", "gt", "lt", "gte", "lte", "in", "between", "contains"] as const;
const OPEN_MODES = ["same_tab", "new_tab", "presentation"] as const;

type Props = {
  dashboardId: string;
  widget: DashboardWidget;
  onClose: () => void;
  onUpdateWidget: (widget: DashboardWidget) => void;
};

type TabId = "data" | "style" | "filters" | "drill" | "interactions" | "export";

export function WidgetConfigDrawer({
  dashboardId,
  widget,
  onClose,
  onUpdateWidget,
  onDuplicate,
}: Props & { onDuplicate?: () => void }) {
  const [tab, setTab] = useState<TabId>("data");
  const qc = useQueryClient();
  const { variables, globalFilters, getWidgetExtraFilters } = useDashboardFilters();

  const bindings = (widget.settings.variable_filters ||
    widget.settings.filters ||
    []) as WidgetVariableFilter[];

  const { data: dashboards = [] } = useQuery({
    queryKey: ["dashboards"],
    queryFn: () => api.listDashboards(),
    enabled: tab === "drill",
  });

  const { data: drillRules = [] } = useQuery({
    queryKey: ["drillthrough", dashboardId],
    queryFn: () => api.listDrillthroughRules(dashboardId),
  });

  const widgetRules = drillRules.filter(
    (r) => !r.source_widget_id || r.source_widget_id === widget.id
  );

  const extraFilters = useMemo(
    () => [...globalFilters, ...getWidgetExtraFilters(widget.settings)],
    [globalFilters, getWidgetExtraFilters, widget.settings]
  );

  const { data: countData, isFetching: counting } = useQuery({
    queryKey: ["filtered-count-preview", widget.dataset_id, extraFilters],
    queryFn: () => api.filteredCount(widget.dataset_id!, extraFilters),
    enabled: !!widget.dataset_id && tab === "filters",
  });

  const createDrill = useMutation({
    mutationFn: (body: Omit<DashboardDrillthroughRule, "id" | "source_dashboard_id">) =>
      api.createDrillthroughRule(dashboardId, body),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["drillthrough", dashboardId] }),
  });

  const deleteDrill = useMutation({
    mutationFn: (ruleId: string) => api.deleteDrillthroughRule(dashboardId, ruleId),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["drillthrough", dashboardId] }),
  });

  const setBindings = (next: WidgetVariableFilter[]) => {
    onUpdateWidget({
      ...widget,
      settings: { ...widget.settings, variable_filters: next },
    });
  };

  const ds = widget.dataset_id;

  const { data: datasetDetail } = useQuery({
    queryKey: ["dataset", ds],
    queryFn: () => api.getDataset(ds!),
    enabled: !!ds,
  });

  const colNames = datasetDetail?.columns?.map((c) => c.name) ?? [];

  return (
    <div className="fixed inset-0 z-[250] flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-md flex-col border-l border-forge-border bg-forge-surface shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-forge-border px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-forge-text">Widget configuration</p>
            <p className="text-xs text-forge-muted">{widget.widget_type}</p>
          </div>
          <button type="button" onClick={onClose} className="text-forge-muted hover:text-forge-text">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-wrap border-b border-forge-border">
          {(
            [
              ["data", "Data"],
              ["style", "Style"],
              ["filters", "Filters"],
              ["drill", "Drill"],
              ["interactions", "Interact"],
              ["export", "Export"],
            ] as const
          ).map(([t, label]) => (
            <button
              key={t}
              type="button"
              className={`px-3 py-2 text-xs ${tab === t ? "border-b-2 border-forge-text font-medium text-forge-text" : "text-forge-muted"}`}
              onClick={() => setTab(t)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {tab === "data" && (
            <div className="space-y-3 text-sm">
              <label className="block text-xs text-forge-muted">Title</label>
              <input
                className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5"
                value={String(widget.settings.title ?? widget.widget_type)}
                onChange={(e) =>
                  onUpdateWidget({
                    ...widget,
                    settings: { ...widget.settings, title: e.target.value },
                  })
                }
              />
              <label className="block text-xs text-forge-muted">X column</label>
              <input
                className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5"
                value={String(widget.settings.x_column ?? "")}
                onChange={(e) =>
                  onUpdateWidget({
                    ...widget,
                    settings: { ...widget.settings, x_column: e.target.value },
                  })
                }
              />
              <label className="block text-xs text-forge-muted">Y column</label>
              <input
                className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5"
                value={String(widget.settings.y_column ?? "")}
                onChange={(e) =>
                  onUpdateWidget({
                    ...widget,
                    settings: { ...widget.settings, y_column: e.target.value },
                  })
                }
              />
              {widget.widget_type === "forecast" && (
                <>
                  <label className="block text-xs text-forge-muted">Date column</label>
                  <input
                    className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5"
                    value={String(widget.settings.date_column ?? "date")}
                    onChange={(e) =>
                      onUpdateWidget({
                        ...widget,
                        settings: { ...widget.settings, date_column: e.target.value },
                      })
                    }
                  />
                  <label className="block text-xs text-forge-muted">Method</label>
                  <select
                    className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5"
                    value={String(widget.settings.method ?? "linear")}
                    onChange={(e) =>
                      onUpdateWidget({
                        ...widget,
                        settings: { ...widget.settings, method: e.target.value },
                      })
                    }
                  >
                    {["linear", "exponential", "holt_winters", "arima", "prophet"].map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </>
              )}
            </div>
          )}

          {tab === "style" && (
            <div className="space-y-3 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={Boolean(widget.settings.locked)}
                  onChange={(e) =>
                    onUpdateWidget({
                      ...widget,
                      settings: { ...widget.settings, locked: e.target.checked },
                    })
                  }
                />
                Lock position (no drag)
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={Boolean(widget.settings.hidden)}
                  onChange={(e) =>
                    onUpdateWidget({
                      ...widget,
                      settings: { ...widget.settings, hidden: e.target.checked },
                    })
                  }
                />
                Hide widget on dashboard
              </label>
            </div>
          )}

          {tab === "interactions" && (
            <p className="text-xs text-forge-muted">
              Click chart segments to cross-filter (no drill rule) or navigate when a drill-through
              rule exists. Enable “Drill available” badge via Drill tab.
            </p>
          )}

          {tab === "export" && (
            <p className="text-xs text-forge-muted">
              Use dashboard toolbar Export PNG/PDF, or Chart Studio for per-chart SVG. Forecast
              widgets support CSV export from the widget body.
            </p>
          )}

          {tab === "filters" && (
            <div className="space-y-4">
              <p className="text-xs text-forge-muted">
                Bind dashboard variables to dataset columns. Filters run server-side (DuckDB/Polars).
              </p>
              {bindings.map((b, i) => (
                <div key={i} className="space-y-2 rounded-lg border border-forge-border p-3">
                  <label className="block text-xs text-forge-muted">Variable</label>
                  <select
                    className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
                    value={b.variable_id}
                    onChange={(e) => {
                      const next = [...bindings];
                      next[i] = { ...b, variable_id: e.target.value };
                      setBindings(next);
                    }}
                  >
                    <option value="">Select…</option>
                    {variables.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.label || v.name}
                      </option>
                    ))}
                  </select>
                  <label className="block text-xs text-forge-muted">Column</label>
                  <select
                    className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
                    value={b.column}
                    onChange={(e) => {
                      const next = [...bindings];
                      next[i] = { ...b, column: e.target.value };
                      setBindings(next);
                    }}
                  >
                    <option value="">Select…</option>
                    {colNames.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <label className="block text-xs text-forge-muted">Operator</label>
                  <select
                    className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
                    value={b.operator}
                    onChange={(e) => {
                      const next = [...bindings];
                      next[i] = { ...b, operator: e.target.value };
                      setBindings(next);
                    }}
                  >
                    {OPERATORS.map((op) => (
                      <option key={op} value={op}>
                        {op}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="ghost"
                    className="w-full text-xs"
                    onClick={() => setBindings(bindings.filter((_, j) => j !== i))}
                  >
                    <Trash2 className="h-3 w-3" /> Remove
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                className="w-full"
                onClick={() =>
                  setBindings([
                    ...bindings,
                    { variable_id: variables[0]?.id ?? "", column: colNames[0] ?? "", operator: "eq" },
                  ])
                }
              >
                <Plus className="h-4 w-4" /> Add binding
              </Button>
              <p className="rounded-lg bg-forge-hover px-3 py-2 text-sm tabular-nums text-forge-text">
                {counting ? "Counting…" : `${(countData?.total_rows ?? 0).toLocaleString()} rows match`}
              </p>
            </div>
          )}

          {tab === "drill" && (
            <div className="space-y-4">
              <p className="text-xs text-forge-muted">
                Click a chart segment to open another dashboard with the selected value in the URL.
              </p>
              {widgetRules.map((r) => (
                <div key={r.id} className="rounded-lg border border-forge-border p-3 text-sm">
                  <p className="font-medium text-forge-text">{r.label}</p>
                  <p className="text-xs text-forge-muted">
                    {r.trigger_column} → {r.target_variable_name}
                  </p>
                  <Button
                    variant="ghost"
                    className="mt-2 text-xs"
                    onClick={() => deleteDrill.mutate(r.id)}
                  >
                    <Trash2 className="h-3 w-3" /> Delete
                  </Button>
                </div>
              ))}
              <DrillRuleForm
                widgetId={widget.id}
                dashboards={dashboards.filter((d) => d.id !== dashboardId)}
                variables={variables}
                colNames={colNames}
                onSubmit={(body) => createDrill.mutate(body)}
                loading={createDrill.isPending}
              />
            </div>
          )}
        </div>

        <div className="border-t border-forge-border p-3 flex gap-2">
          {onDuplicate && (
            <Button variant="secondary" className="flex-1 text-xs" onClick={onDuplicate}>
              Duplicate
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function DrillRuleForm({
  widgetId,
  dashboards,
  variables,
  colNames,
  onSubmit,
  loading,
}: {
  widgetId?: string;
  dashboards: { id: string; name: string }[];
  variables: { name: string }[];
  colNames: string[];
  onSubmit: (body: Omit<DashboardDrillthroughRule, "id" | "source_dashboard_id">) => void;
  loading: boolean;
}) {
  const [label, setLabel] = useState("Drill through");
  const [trigger, setTrigger] = useState(colNames[0] ?? "");
  const [targetDash, setTargetDash] = useState(dashboards[0]?.id ?? "");
  const [targetVar, setTargetVar] = useState("");
  const [openMode, setOpenMode] = useState<string>("same_tab");

  return (
    <div className="space-y-2 rounded-lg border border-dashed border-forge-border p-3">
      <input
        className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
        placeholder="Label"
        value={label}
        onChange={(e) => setLabel(e.target.value)}
      />
      <select
        className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
        value={trigger}
        onChange={(e) => setTrigger(e.target.value)}
      >
        {colNames.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <select
        className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
        value={targetDash}
        onChange={(e) => setTargetDash(e.target.value)}
      >
        {dashboards.map((d) => (
          <option key={d.id} value={d.id}>
            {d.name}
          </option>
        ))}
      </select>
      <input
        className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
        placeholder="Target variable name on destination dashboard"
        value={targetVar}
        onChange={(e) => setTargetVar(e.target.value)}
      />
      <select
        className="w-full rounded border border-forge-border bg-forge-bg px-2 py-1.5 text-sm"
        value={openMode}
        onChange={(e) => setOpenMode(e.target.value)}
      >
        {OPEN_MODES.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
      <Button
        className="w-full"
        loading={loading}
        disabled={!targetDash || !targetVar || !trigger}
        onClick={() =>
          onSubmit({
            source_widget_id: widgetId ?? null,
            target_dashboard_id: targetDash,
            trigger_column: trigger,
            target_variable_name: targetVar,
            label,
            open_mode: openMode,
          })
        }
      >
        <Plus className="h-4 w-4" /> Add drill-through rule
      </Button>
    </div>
  );
}
