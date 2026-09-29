"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DatasetSubNav } from "@/components/layout/sidebar";
import { Card } from "@/components/ui/card";
import { formatBytes, formatNumber } from "@/lib/utils";
import { useDatasetRoute } from "@/hooks/use-dataset-route";
import { InsightsPanel } from "@/components/enterprise/insights-panel";
import { ForecastPanel } from "@/components/enterprise/forecast-panel";
import { AnomalyPanel } from "@/components/enterprise/anomaly-panel";

export default function DatasetOverviewPage() {
  const { id, ready, isPlaceholder } = useDatasetRoute();
  const { data: dataset, isLoading } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id),
    enabled: ready,
  });

  if (isPlaceholder) return null;

  if (isLoading || !dataset) {
    return <p className="text-forge-muted">Loading…</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-forge-text">{dataset.name}</h1>
      <DatasetSubNav datasetId={id} />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-2xl font-bold tabular-nums text-forge-text">{formatNumber(dataset.row_count)}</p>
          <p className="text-xs text-forge-muted">Rows</p>
        </Card>
        <Card>
          <p className="text-2xl font-bold">{dataset.column_count}</p>
          <p className="text-xs text-forge-muted">Columns</p>
        </Card>
        <Card>
          <p className="text-2xl font-bold">{formatBytes(dataset.file_size_bytes)}</p>
          <p className="text-xs text-forge-muted">File size</p>
        </Card>
      </div>

      {dataset.status === "ready" && (
        <div className="mt-6 grid gap-6 lg:grid-cols-1">
          <InsightsPanel datasetId={id} />
          <ForecastPanel dataset={dataset} />
          <AnomalyPanel datasetId={id} />
        </div>
      )}

      <Card title="Columns" className="mt-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-forge-muted">
                <th className="py-2">Name</th>
                <th>Type</th>
              </tr>
            </thead>
            <tbody>
              {dataset.columns.map((c) => (
                <tr key={c.name} className="border-t border-forge-border">
                  <td className="py-2">{c.name}</td>
                  <td className="text-forge-muted">{c.dtype}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
