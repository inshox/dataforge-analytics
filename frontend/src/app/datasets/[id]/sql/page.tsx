"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DatasetSubNav } from "@/components/layout/sidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDatasetRoute } from "@/hooks/use-dataset-route";

const DEFAULT_SQL = "SELECT * FROM dataset LIMIT 100";

export default function SqlLabPage() {
  const { id, ready, isPlaceholder } = useDatasetRoute();
  const [query, setQuery] = useState(DEFAULT_SQL);
  const [submitted, setSubmitted] = useState(DEFAULT_SQL);

  const { data: dataset } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => api.getDataset(id),
    enabled: ready,
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["sql", id, submitted],
    queryFn: () => api.runSql(id, submitted),
    enabled: ready && dataset?.status === "ready",
    retry: false,
  });

  if (isPlaceholder) return null;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold text-forge-text">SQL Lab — {dataset?.name}</h1>
      <DatasetSubNav datasetId={id} />

      <Card title="Query (DuckDB)">
        <p className="mb-2 text-xs text-forge-muted">
          Table <code className="text-indigo-300">dataset</code> references your imported Parquet file.
        </p>
        <textarea
          className="mb-3 h-32 w-full rounded-lg border border-forge-border bg-forge-surface p-3 font-mono text-sm"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button onClick={() => { setSubmitted(query); void refetch(); }} loading={isLoading}>
          Run query
        </Button>
        {error && <p className="mt-2 text-sm text-red-400">{(error as Error).message}</p>}
      </Card>

      {data && (
        <Card title={`Results (${data.total_rows} rows)`} className="mt-6">
          <div className="max-h-96 overflow-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  {data.columns.map((c) => (
                    <th key={c} className="border-b border-forge-border px-2 py-2 text-left">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, i) => (
                  <tr key={i} className="border-b border-forge-border/50">
                    {data.columns.map((c) => (
                      <td key={c} className="px-2 py-1">
                        {String(row[c] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
