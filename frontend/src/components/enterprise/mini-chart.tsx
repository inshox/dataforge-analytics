"use client";

import type { DatasetSummary } from "@/lib/api";
import { ChartRenderer } from "@/components/charts/chart-renderer";

export function MiniChart({
  dataset,
  chartType = "bar",
  xColumn,
  yColumn,
  aggregation = "sum",
  sourceColumn,
  targetColumn,
}: {
  dataset: DatasetSummary;
  chartType?: string;
  xColumn?: string;
  yColumn?: string;
  aggregation?: string;
  sourceColumn?: string;
  targetColumn?: string;
}) {
  const x = xColumn || dataset.columns[0]?.name || "";
  const y = yColumn || dataset.columns[1]?.name;

  return (
    <ChartRenderer
      dataset={dataset}
      height={180}
      params={{
        chartType,
        xColumn: x,
        yColumn: y,
        sourceColumn,
        targetColumn,
        aggregation,
        limit: 24,
      }}
    />
  );
}
