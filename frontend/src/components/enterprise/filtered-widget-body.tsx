"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type DashboardWidget, type DatasetSummary } from "@/lib/api";
import { useDashboardFilters } from "@/contexts/dashboard-filter-context";
import { ChartRenderer } from "@/components/charts/chart-renderer";
import { DashboardForecastWidget } from "@/components/enterprise/dashboard-forecast-widget";
import { DashboardAnomalyWidget } from "@/components/enterprise/dashboard-anomaly-widget";
import { buildDrillthroughHref } from "@/lib/dashboard-filters";
import { useRouter } from "next/navigation";

type Props = {
  dashboardId: string;
  widget: DashboardWidget;
  dataset?: DatasetSummary;
  drillRules?: import("@/lib/api").DashboardDrillthroughRule[];
  liveRefresh?: boolean;
};

export function FilteredWidgetBody({
  dashboardId: _dashboardId,
  widget,
  dataset,
  drillRules = [],
  liveRefresh = false,
}: Props) {
  const router = useRouter();
  const { variables, globalFilters, getWidgetExtraFilters, applyCrossFilter, filterVersion } =
    useDashboardFilters();

  const extraFilters = useMemo(
    () => [...globalFilters, ...getWidgetExtraFilters(widget.settings)],
    [globalFilters, getWidgetExtraFilters, widget.settings, filterVersion]
  );

  const pollMs = liveRefresh ? 5000 : false;

  const { data: countData } = useQuery({
    queryKey: ["filtered-count", dataset?.id, extraFilters, filterVersion],
    queryFn: () => api.filteredCount(dataset!.id, extraFilters),
    enabled: !!dataset?.id,
    refetchInterval: pollMs,
  });

  if (widget.settings.hidden) {
    return null;
  }

  if (widget.widget_type === "forecast") {
    if (!dataset) return <p className="p-4 text-xs text-forge-muted">No dataset</p>;
    return (
      <DashboardForecastWidget
        dataset={dataset}
        settings={widget.settings}
        extraFilters={extraFilters}
        liveRefresh={liveRefresh}
      />
    );
  }

  if (widget.widget_type === "anomaly") {
    if (!dataset) return <p className="p-4 text-xs text-forge-muted">No dataset</p>;
    return (
      <DashboardAnomalyWidget
        dataset={dataset}
        extraFilters={extraFilters}
        liveRefresh={liveRefresh}
      />
    );
  }

  if (widget.widget_type === "kpi") {
    const metricCol = String(widget.settings.metric_column ?? widget.settings.column ?? "revenue");
    const agg = String(widget.settings.aggregation ?? "sum");
    return (
      <KpiWidget
        dataset={dataset}
        label={String(widget.settings.label ?? "KPI")}
        metricCol={metricCol}
        agg={agg}
        extraFilters={extraFilters}
        count={countData?.total_rows}
        liveRefresh={liveRefresh}
      />
    );
  }

  if (!dataset) {
    return <p className="p-4 text-xs text-forge-muted">No dataset</p>;
  }

  if (widget.widget_type === "table") {
    return (
      <p className="p-4 text-sm text-forge-muted">
        Table · {countData?.total_rows ?? "—"} rows match filters
      </p>
    );
  }

  const chartType = widget.chart_type ?? widget.widget_type;
  const xCol = String(widget.settings.x_column ?? "");
  const yCol = String(widget.settings.y_column ?? "");

  const columnToVariable = (col: string) => {
    const rules = drillRules.filter((r) => r.trigger_column === col);
    return rules;
  };

  const hasDrill = drillRules.some(
    (r) => r.trigger_column === xCol && (!r.source_widget_id || r.source_widget_id === widget.id)
  );

  return (
    <ChartRenderer
      dataset={dataset}
      height={160}
      liveRefresh={liveRefresh}
      drillAvailable={hasDrill}
      params={{
        chartType: chartType === "gauge" || chartType === "radar" ? "bar" : chartType,
        xColumn: xCol,
        yColumn: yCol,
        sourceColumn: String(widget.settings.source_column ?? ""),
        targetColumn: String(widget.settings.target_column ?? ""),
        aggregation: String(widget.settings.aggregation ?? "sum"),
        limit: 24,
        config: widget.settings as Record<string, unknown>,
        extra_filters: extraFilters,
      }}
      onDataPointClick={(label, column) => {
        const col = column || xCol;
        const rule = columnToVariable(col)[0];
        if (rule) {
          const href = buildDrillthroughHref(
            rule.target_dashboard_id,
            rule.target_variable_name,
            label
          );
          router.push(rule.open_mode === "presentation" ? `${href}&present=1` : href);
          return;
        }
        const matched = variables.find((v) => v.column_name === col || v.name === col);
        applyCrossFilter(matched?.name ?? col, label);
      }}
    />
  );
}

function KpiWidget({
  dataset,
  label,
  metricCol,
  agg,
  extraFilters,
  count,
  liveRefresh,
}: {
  dataset?: DatasetSummary;
  label: string;
  metricCol: string;
  agg: string;
  extraFilters: import("@/lib/api").FilterCondition[];
  count?: number;
  liveRefresh?: boolean;
}) {
  const pollMs = liveRefresh ? 5000 : false;
  const { data } = useQuery({
    queryKey: ["kpi", dataset?.id, metricCol, agg, extraFilters],
    queryFn: () =>
      api.buildChart(dataset!.id, {
        chart_type: "bar",
        x_column: metricCol,
        y_column: metricCol,
        aggregation: agg,
        extra_filters: extraFilters,
        limit: 1,
      }),
    enabled: !!dataset?.id,
    refetchInterval: pollMs,
  });

  const value = data?.data[0]?.value ?? count ?? "—";

  return (
    <div className="flex h-full flex-col justify-center px-4 py-6">
      <p className="text-xs text-forge-muted">{label}</p>
      <p className="text-2xl font-bold tabular-nums text-forge-text">{value}</p>
      {count !== undefined && (
        <p className="text-[10px] text-forge-muted">{count.toLocaleString()} rows</p>
      )}
    </div>
  );
}
