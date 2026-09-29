"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { api, type ChartResponse, type DatasetSummary } from "@/lib/api";
import { SankeyChart } from "@/components/charts/advanced/sankey-chart";
import { FunnelChart } from "@/components/charts/advanced/funnel-chart";
import { CandlestickChart } from "@/components/charts/advanced/candlestick-chart";
import { TreemapChart } from "@/components/charts/advanced/treemap-chart";
import { WaterfallChart } from "@/components/charts/advanced/waterfall-chart";
import { exportElementAsPng, exportElementAsSvg } from "@/lib/chart-export";
import { Button } from "@/components/ui/button";

export type ChartBuildParams = {
  chartType: string;
  xColumn: string;
  yColumn?: string;
  zColumn?: string;
  sourceColumn?: string;
  targetColumn?: string;
  parentColumn?: string;
  aggregation?: string;
  limit?: number;
  config?: Record<string, unknown>;
};

type Props = {
  dataset: DatasetSummary;
  params: ChartBuildParams & { extra_filters?: import("@/lib/api").FilterCondition[] };
  height?: number;
  showExport?: boolean;
  onData?: (data: ChartResponse) => void;
  onDataPointClick?: (label: string, column?: string) => void;
  liveRefresh?: boolean;
  drillAvailable?: boolean;
};

export function ChartRenderer({
  dataset,
  params,
  height = 360,
  showExport = false,
  onData,
  onDataPointClick,
  liveRefresh = false,
  drillAvailable = false,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const { data, isLoading } = useQuery({
    queryKey: ["chart", dataset.id, params],
    queryFn: () =>
      api.buildChart(dataset.id, {
        chart_type: params.chartType,
        x_column: params.xColumn,
        y_column: params.yColumn,
        z_column: params.zColumn,
        source_column: params.sourceColumn,
        target_column: params.targetColumn,
        parent_column: params.parentColumn,
        aggregation: params.aggregation ?? "sum",
        limit: params.limit ?? 100,
        config: params.config ?? {},
        extra_filters: params.extra_filters ?? [],
      }),
    enabled: !!params.xColumn && mounted,
    refetchInterval: liveRefresh ? 5000 : false,
  });

  useEffect(() => {
    if (data && onData) onData(data);
  }, [data, onData]);

  if (!mounted || isLoading) {
    return <p className="py-12 text-center text-sm text-forge-muted">Loading chart…</p>;
  }
  if (!data || !data.data?.length) {
    return (
      <p className="py-12 text-center text-sm text-forge-muted">
        No data for current filters. Adjust variables or widget bindings.
      </p>
    );
  }

  const chartData = data.data.map((d) => ({ name: d.label, value: d.value, ...d.extra }));

  return (
    <div className="relative">
      {drillAvailable && (
        <span className="absolute right-2 top-2 z-10 rounded bg-forge-accent-soft px-1.5 py-0.5 text-[9px] text-forge-muted">
          Drill available
        </span>
      )}
      {showExport && (
        <div className="mb-2 flex gap-2">
          <Button
            variant="secondary"
            onClick={() => ref.current && void exportElementAsPng(ref.current, "chart.png")}
          >
            PNG
          </Button>
          <Button
            variant="secondary"
            onClick={() => ref.current && exportElementAsSvg(ref.current, "chart.svg")}
          >
            SVG
          </Button>
        </div>
      )}
      <div ref={ref} style={{ height }} className="w-full min-w-0">
        {renderChart(data, chartData, params.chartType, onDataPointClick, params.xColumn)}
      </div>
    </div>
  );
}

function renderChart(
  response: ChartResponse,
  chartData: { name: string; value: number }[],
  chartType: string,
  onDataPointClick?: (label: string, column?: string) => void,
  xColumn?: string
) {
  const clickProps = onDataPointClick
    ? {
        onClick: (state: { activeLabel?: string }) => {
          if (state?.activeLabel) onDataPointClick(String(state.activeLabel), xColumn);
        },
        style: { cursor: "pointer" },
      }
    : {};
  const t = chartType.toLowerCase();
  if (t === "sankey" || t === "network") {
    return <SankeyChart nodes={response.nodes ?? []} links={response.links ?? []} />;
  }
  if (t === "funnel") {
    return <FunnelChart data={response.data} />;
  }
  if (t === "candlestick") {
    return <CandlestickChart series={response.series as never[]} />;
  }
  if (t === "treemap" || t === "sunburst") {
    return <TreemapChart nodes={response.nodes ?? []} />;
  }
  if (t === "waterfall") {
    return <WaterfallChart data={response.data} />;
  }
  if (t === "bubble") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart>
          <XAxis dataKey="x" name="x" tick={{ fontSize: 10 }} />
          <YAxis dataKey="y" name="y" tick={{ fontSize: 10 }} />
          <ZAxis dataKey="z" range={[40, 400]} />
          <Tooltip />
          <Scatter data={chartData.map((d) => d as Record<string, unknown>)} fill="var(--forge-text)" />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }
  if (t === "pie") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <PieChart {...clickProps}>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius="80%"
            onClick={(_, index) => {
              const row = chartData[index];
              if (row && onDataPointClick) onDataPointClick(row.name, xColumn);
            }}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={`hsl(${i * 40}, 50%, 55%)`} style={{ cursor: onDataPointClick ? "pointer" : undefined }} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  }
  if (t === "line" || t === "area") {
    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} {...clickProps}>
          <CartesianGrid stroke="var(--forge-border)" strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="var(--forge-text)" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} {...clickProps}>
        <CartesianGrid stroke="var(--forge-border)" strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip />
        <Bar dataKey="value" fill="var(--forge-text)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
