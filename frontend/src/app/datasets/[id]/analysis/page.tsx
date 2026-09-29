"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DatasetSubNav } from "@/components/layout/sidebar";
import { Card } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";
import { useDatasetRoute } from "@/hooks/use-dataset-route";

export default function AnalysisPage() {
  const { id, ready, isPlaceholder } = useDatasetRoute();
  const { data: dataset } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id),
    enabled: ready,
  });
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile", id],
    queryFn: () => api.getProfile(id),
    enabled: ready && dataset?.status === "ready",
  });

  if (isPlaceholder) return null;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-forge-text">Data profile — {dataset?.name}</h1>
      <DatasetSubNav datasetId={id} />

      {isLoading ? (
        <p className="text-forge-muted">Computing profile…</p>
      ) : profile ? (
        <>
          <div className="mb-6 grid gap-4 md:grid-cols-4">
            <Card>
              <p className="text-2xl font-bold tabular-nums text-forge-text">{formatNumber(profile.row_count)}</p>
              <p className="text-xs text-forge-muted">Rows</p>
            </Card>
            <Card>
              <p className="text-2xl font-bold tabular-nums text-forge-text">{formatNumber(profile.duplicate_rows)}</p>
              <p className="text-xs text-forge-muted">Duplicate rows</p>
            </Card>
            <Card>
              <p className="text-2xl font-bold tabular-nums text-forge-text">{profile.column_count}</p>
              <p className="text-xs text-forge-muted">Columns</p>
            </Card>
            <Card>
              <p className="text-2xl font-bold tabular-nums text-forge-text">{profile.correlations.length}</p>
              <p className="text-xs text-forge-muted">Numeric correlations</p>
            </Card>
          </div>

          {profile.insights.length > 0 && (
            <Card title="Insights" className="mb-6">
              <ul className="list-inside list-disc space-y-1 text-sm text-forge-text">
                {profile.insights.map((ins) => (
                  <li key={ins}>{ins}</li>
                ))}
              </ul>
            </Card>
          )}

          <Card title="Column profiling" className="mb-6">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-forge-muted">
                    <th className="py-2 pr-4">Column</th>
                    <th>Inferred</th>
                    <th>Missing</th>
                    <th>Unique</th>
                    <th>Outliers</th>
                    <th>Top values</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.columns.map((c) => (
                    <tr key={c.column} className="border-t border-forge-border">
                      <td className="py-2 pr-4 font-medium text-forge-text">{c.column}</td>
                      <td className="text-forge-muted">{c.inferred_type}</td>
                      <td className="tabular-nums text-forge-text">
                        {c.null_count} ({c.null_percent}%)
                      </td>
                      <td className="tabular-nums text-forge-text">{c.unique_count}</td>
                      <td className="tabular-nums text-forge-text">{c.outlier_count || "—"}</td>
                      <td className="max-w-xs truncate text-xs text-forge-muted">
                        {c.top_values.map((t) => `${t.value} (${t.count})`).join(", ") || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {profile.correlations.length > 0 && (
            <Card title="Correlations (numeric)">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-forge-muted">
                      <th className="py-2 text-left">A</th>
                      <th className="py-2 text-left">B</th>
                      <th className="py-2 text-left">r</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profile.correlations.map((cr) => (
                      <tr key={`${cr.column_a}-${cr.column_b}`} className="border-t border-forge-border">
                        <td className="py-2 text-forge-text">{cr.column_a}</td>
                        <td className="py-2 text-forge-text">{cr.column_b}</td>
                        <td className="py-2 font-mono tabular-nums text-forge-text">{cr.correlation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
}
