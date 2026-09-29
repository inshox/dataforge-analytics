"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ChartDataPoint } from "@/lib/api";

export function WaterfallChart({ data }: { data: ChartDataPoint[] }) {
  const chartData = data.map((d) => ({
    name: d.label,
    value: d.value,
    cumulative: Number(d.extra?.cumulative ?? d.value),
    positive: d.extra?.positive !== false,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData}>
        <XAxis dataKey="name" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip />
        <Bar dataKey="value">
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.positive ? "#22c55e" : "#ef4444"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
