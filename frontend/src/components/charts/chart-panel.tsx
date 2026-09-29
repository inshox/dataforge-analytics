"use client";

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
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DatasetSummary } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useEffect, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { exportElementAsPng, exportElementAsSvg } from "@/lib/chart-export";

const COLORS = ["#6366f1", "#22d3ee", "#a78bfa", "#34d399", "#f472b6", "#fbbf24"];

export function ChartPanel({ dataset }: { dataset: DatasetSummary }) {
  const cols = dataset.columns.map((c) => c.name);
  const [chartType, setChartType] = useState("bar");
  const [xCol, setXCol] = useState("");
  const [yCol, setYCol] = useState("");
  const [agg, setAgg] = useState("count");
  const [mounted, setMounted] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const names = dataset.columns.map((c) => c.name);
    setXCol(names[0] || "");
    setYCol(names[1] || names[0] || "");
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reset columns only when dataset changes
  }, [dataset.id]);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["chart", dataset.id, chartType, xCol, yCol, agg],
    queryFn: () =>
      api.buildChart(dataset.id, {
        chart_type: chartType,
        x_column: xCol,
        y_column: yCol,
        aggregation: agg,
      }),
    enabled: !!xCol,
  });

  const chartData = data?.data.map((d) => ({ name: d.label, value: d.value })) ?? [];

  return (
    <div className="space-y-6">
      <Card title="Chart builder">
        <div className="flex flex-wrap gap-3">
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            value={chartType}
            onChange={(e) => setChartType(e.target.value)}
          >
            <option value="bar">Bar</option>
            <option value="line">Line</option>
            <option value="pie">Pie</option>
          </select>
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            value={xCol}
            onChange={(e) => setXCol(e.target.value)}
          >
            {cols.map((c) => (
              <option key={c} value={c}>
                X: {c}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            value={yCol}
            onChange={(e) => setYCol(e.target.value)}
          >
            {cols.map((c) => (
              <option key={c} value={c}>
                Y: {c}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            value={agg}
            onChange={(e) => setAgg(e.target.value)}
          >
            <option value="count">Count</option>
            <option value="sum">Sum</option>
            <option value="mean">Mean</option>
            <option value="min">Min</option>
            <option value="max">Max</option>
          </select>
          <Button variant="secondary" onClick={() => refetch()}>
            Refresh
          </Button>
        </div>
      </Card>

      <Card title="Visualization">
        <div className="mb-2 flex gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              if (chartRef.current) void exportElementAsPng(chartRef.current, `${dataset.name}-chart.png`);
            }}
          >
            Export PNG
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              if (chartRef.current) exportElementAsSvg(chartRef.current, `${dataset.name}-chart.svg`);
            }}
          >
            Export SVG
          </Button>
        </div>
        {isLoading ? (
          <p className="py-12 text-center text-forge-muted">Loading chart…</p>
        ) : chartData.length === 0 ? (
          <p className="py-12 text-center text-forge-muted">No data</p>
        ) : !mounted ? (
          <p className="py-12 text-center text-forge-muted">Loading chart…</p>
        ) : (
          <div ref={chartRef} className="h-96 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%" debounce={100} minWidth={0}>
              {chartType === "pie" ? (
                <PieChart>
                  <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={120}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              ) : chartType === "line" ? (
                <LineChart data={chartData}>
                  <CartesianGrid stroke="rgba(148,163,184,0.15)" />
                  <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={false} />
                </LineChart>
              ) : (
                <BarChart data={chartData}>
                  <CartesianGrid stroke="rgba(148,163,184,0.15)" />
                  <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </Card>
    </div>
  );
}
