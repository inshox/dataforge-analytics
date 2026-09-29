"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useDatasetRoute } from "@/hooks/use-dataset-route";
import { DatasetSubNav } from "@/components/layout/sidebar";
import { AiAnalystPanel } from "@/components/data/ai-analyst-panel";

export default function AnalystPage() {
  const { id, ready, isPlaceholder } = useDatasetRoute();
  const { data: dataset } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id),
    enabled: ready,
  });

  if (isPlaceholder) return null;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-forge-text">AI Analyst — {dataset?.name}</h1>
      <DatasetSubNav datasetId={id} />
      {dataset?.status === "ready" ? (
        <AiAnalystPanel datasetId={id} />
      ) : (
        <p className="text-forge-muted">Dataset must be ready before using AI Analyst.</p>
      )}
    </div>
  );
}
