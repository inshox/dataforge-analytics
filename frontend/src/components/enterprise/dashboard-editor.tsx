"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save, Download, GripVertical, Image, Maximize2, Settings2, Radio } from "lucide-react";
import { WidgetConfigDrawer } from "@/components/enterprise/widget-config-drawer";
import { api, type DashboardWidget, type DatasetSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { DashboardGrid } from "@/components/enterprise/dashboard-grid";
import { DashboardFilterBar } from "@/components/enterprise/dashboard-filter-bar";
import { DashboardActiveFilters } from "@/components/enterprise/dashboard-active-filters";
import { DashboardDrillBreadcrumbs } from "@/components/enterprise/dashboard-drill-breadcrumbs";
import { FilteredWidgetBody } from "@/components/enterprise/filtered-widget-body";
import { exportElementAsPng } from "@/lib/chart-export";

const WIDGET_TYPES = [
  "kpi",
  "bar",
  "line",
  "area",
  "pie",
  "scatter",
  "histogram",
  "heatmap",
  "treemap",
  "boxplot",
  "gauge",
  "radar",
  "waterfall",
  "table",
  "forecast",
  "anomaly",
];

export function DashboardEditor({ dashboardId }: { dashboardId: string }) {
  const qc = useQueryClient();
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [name, setName] = useState("");
  const [presenting, setPresenting] = useState(false);
  const [liveRefresh, setLiveRefresh] = useState(false);
  const [configWidgetId, setConfigWidgetId] = useState<string | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard", dashboardId],
    queryFn: () => api.getDashboard(dashboardId),
    enabled: !!dashboardId,
  });

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });

  const { data: drillRules = [] } = useQuery({
    queryKey: ["drillthrough", dashboardId],
    queryFn: () => api.listDrillthroughRules(dashboardId),
  });

  useEffect(() => {
    if (dashboard) {
      setWidgets(dashboard.widgets);
      setName(dashboard.name);
    }
  }, [dashboard]);

  const save = useMutation({
    mutationFn: () => api.saveDashboard(dashboardId, { name, widgets }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["dashboard", dashboardId] }),
  });

  const addWidget = (type: string) => {
    const ds = datasets.find((d) => d.status === "ready");
    if (!ds) return;
    const maxY = widgets.reduce((m, w) => Math.max(m, w.y + w.h), 0);
    const w: DashboardWidget = {
      id: `w-${Date.now()}`,
      widget_type: type,
      dataset_id: ds.id,
      chart_type: ["kpi", "table"].includes(type) ? undefined : type,
      x: 0,
      y: maxY,
      w: type === "kpi" ? 3 : 6,
      h: type === "kpi" ? 2 : 4,
      settings:
        type === "kpi"
          ? { label: "Rows", value: ds.row_count }
          : {
              x_column: ds.columns[0]?.name ?? "",
              y_column: ds.columns[1]?.name,
              aggregation: "sum",
            },
    };
    setWidgets((prev) => [...prev, w]);
  };

  if (isLoading || !dashboard) {
    return <p className="text-forge-muted">Loading dashboard…</p>;
  }

  if (presenting) {
    return (
      <div className="fixed inset-0 z-[300] overflow-auto bg-forge-bg p-6">
        <Button className="fixed right-6 top-6 z-[301]" variant="secondary" onClick={() => setPresenting(false)}>
          Exit presentation
        </Button>
        <h1 className="mb-6 text-3xl font-bold text-forge-text">{name}</h1>
        <DashboardGrid
          widgets={widgets}
          onLayoutChange={() => {}}
          renderWidget={(w) => {
            const ds = datasets.find((d) => d.id === w.dataset_id);
            return (
              <FilteredWidgetBody
                dashboardId={dashboardId}
                widget={w}
                dataset={ds}
                drillRules={drillRules}
              />
            );
          }}
        />
      </div>
    );
  }

  return (
    <div ref={gridRef}>
      <DashboardDrillBreadcrumbs dashboardId={dashboardId} />
      <DashboardFilterBar />
      <DashboardActiveFilters />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-lg font-semibold text-forge-text"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <Button loading={save.isPending} onClick={() => save.mutate()}>
          <Save className="h-4 w-4" /> Save
        </Button>
        <Button
          variant="secondary"
          onClick={async () => {
            const url = api.dashboardExportUrl(dashboardId, "pdf");
            const res = await fetch(url, { headers: { Authorization: "Bearer demo-token" } });
            const blob = await res.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `${name}.pdf`;
            a.click();
          }}
        >
          <Download className="h-4 w-4" /> Export PDF
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            if (gridRef.current) void exportElementAsPng(gridRef.current, `${name}-dashboard.png`);
          }}
        >
          <Image className="h-4 w-4" /> Export PNG
        </Button>
        <Button variant="secondary" onClick={() => setPresenting(true)}>
          <Maximize2 className="h-4 w-4" /> Present
        </Button>
        <Button
          variant={liveRefresh ? "primary" : "secondary"}
          onClick={() => setLiveRefresh((v) => !v)}
          title="Simulate live dashboard refresh (local polling)"
        >
          <Radio className="h-4 w-4" /> {liveRefresh ? "Live on" : "Live off"}
        </Button>
        <select
          className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm text-forge-text"
          onChange={(e) => {
            if (e.target.value) addWidget(e.target.value);
            e.target.value = "";
          }}
          defaultValue=""
        >
          <option value="">Add widget…</option>
          {WIDGET_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <p className="mb-3 text-xs text-forge-muted">
        12-column grid — drag by handle, resize corners. Changes preview live until you save.
      </p>

      <DashboardGrid
        widgets={widgets}
        onLayoutChange={setWidgets}
        renderWidget={(w) => {
          const ds = datasets.find((d) => d.id === w.dataset_id);
          return (
            <>
              <div className="widget-drag-handle flex cursor-grab items-center justify-between border-b border-forge-border bg-forge-hover px-2 py-1 active:cursor-grabbing">
                <span className="flex items-center gap-1 text-xs text-forge-muted">
                  <GripVertical className="h-3 w-3" /> {w.widget_type}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    className="rounded p-0.5 text-forge-muted hover:text-forge-text"
                    title="Widget filters & drill-through"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConfigWidgetId(w.id ?? null);
                    }}
                  >
                    <Settings2 className="h-3.5 w-3.5" />
                  </button>
                  <select
                    className="max-w-[120px] rounded border border-forge-border bg-forge-surface px-1 text-[10px]"
                    value={w.dataset_id ?? ""}
                    onChange={(e) =>
                      setWidgets((prev) =>
                        prev.map((x) => (x.id === w.id ? { ...x, dataset_id: e.target.value } : x))
                      )
                    }
                    onClick={(e) => e.stopPropagation()}
                  >
                    {datasets
                      .filter((d) => d.status === "ready")
                      .map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                  </select>
                </div>
              </div>
              <FilteredWidgetBody
                dashboardId={dashboardId}
                widget={w}
                dataset={ds}
                drillRules={drillRules}
                liveRefresh={liveRefresh}
              />
            </>
          );
        }}
      />

      {configWidgetId && widgets.find((w) => w.id === configWidgetId) && (
        <WidgetConfigDrawer
          dashboardId={dashboardId}
          widget={widgets.find((w) => w.id === configWidgetId)!}
          onClose={() => setConfigWidgetId(null)}
          onUpdateWidget={(updated) =>
            setWidgets((prev) => prev.map((w) => (w.id === updated.id ? updated : w)))
          }
          onDuplicate={() => {
            const src = widgets.find((w) => w.id === configWidgetId);
            if (!src) return;
            const copy: DashboardWidget = {
              ...src,
              id: `w-${Date.now()}`,
              x: src.x + 1,
              y: src.y + 1,
              settings: { ...src.settings },
            };
            setWidgets((prev) => [...prev, copy]);
            setConfigWidgetId(copy.id ?? null);
          }}
        />
      )}
    </div>
  );
}
