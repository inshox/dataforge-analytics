"use client";

import { Treemap, ResponsiveContainer } from "recharts";
import type { ChartNode } from "@/lib/api";

export function TreemapChart({ nodes }: { nodes: ChartNode[] }) {
  const data = nodes.map((n) => ({
    name: n.name,
    size: n.value ?? 1,
    fill: n.color ?? "var(--forge-text)",
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <Treemap data={data} dataKey="size" stroke="var(--forge-border)" fill="var(--forge-text)" />
    </ResponsiveContainer>
  );
}
