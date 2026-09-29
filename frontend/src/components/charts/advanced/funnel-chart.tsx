"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ChartDataPoint } from "@/lib/api";

const COLORS = ["#fafafa", "#d4d4d4", "#a3a3a3", "#737373", "#525252"];

export function FunnelChart({ data }: { data: ChartDataPoint[] }) {
  const chartData = data.map((d) => ({
    name: d.label,
    value: d.value,
    drop: Number(d.extra?.drop_percent ?? 0),
    conversion: Number(d.extra?.conversion ?? 0),
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} layout="vertical" margin={{ left: 80 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 10 }} />
        <Tooltip
          formatter={(v: number, _n, p) => [
            `${v} (${p.payload.conversion}% conv, ${p.payload.drop}% drop)`,
            "Value",
          ]}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
