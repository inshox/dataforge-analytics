"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DatasetSubNav } from "@/components/layout/sidebar";
import { ChartPanel } from "@/components/charts/chart-panel";
import { useDatasetRoute } from "@/hooks/use-dataset-route";

export default function ChartsPage() {
  const { id, ready, isPlaceholder } = useDatasetRoute();
  const { data: dataset } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id),
    enabled: ready,
  });

  if (isPlaceholder) return null;
  if (!dataset) return <p className="text-forge-muted">Loading…</p>;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-forge-text">Charts — {dataset.name}</h1>
      <DatasetSubNav datasetId={id} />
      <ChartPanel dataset={dataset} />
    </div>
  );
}
