"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function TransformStudioPage() {
  const [datasetId, setDatasetId] = useState("");
  const [renameFrom, setRenameFrom] = useState("");
  const [renameTo, setRenameTo] = useState("");
  const [preview, setPreview] = useState<{
    columns: { name: string }[];
    rows: Record<string, unknown>[];
    row_count: number;
  } | null>(null);

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });

  const runPreview = async () => {
    if (!datasetId || !renameFrom || !renameTo) return;
    const res = await api.transformPreview(datasetId, [
      { op: "rename", params: { from: renameFrom, to: renameTo } },
    ]);
    setPreview(res);
  };

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-forge-text">Transform Studio</h1>
      <p className="mb-6 text-sm text-forge-muted">
        Power Query–style steps — preview before applying. Pipelines save to the dataset.
      </p>
      <Card title="Rename column" className="max-w-xl">
        <select
          className="mb-3 w-full rounded border border-forge-border bg-forge-surface px-3 py-2 text-sm"
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
        >
          <option value="">Select dataset…</option>
          {datasets
            .filter((d) => d.status === "ready")
            .map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
        </select>
        <div className="mb-3 flex gap-2">
          <input
            className="flex-1 rounded border border-forge-border px-2 py-1.5 text-sm"
            placeholder="From column"
            value={renameFrom}
            onChange={(e) => setRenameFrom(e.target.value)}
          />
          <input
            className="flex-1 rounded border border-forge-border px-2 py-1.5 text-sm"
            placeholder="To column"
            value={renameTo}
            onChange={(e) => setRenameTo(e.target.value)}
          />
        </div>
        <Button onClick={() => void runPreview()}>Preview</Button>
      </Card>
      {preview && (
        <Card title={`Preview · ${preview.row_count.toLocaleString()} rows`} className="mt-4">
          <div className="overflow-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  {preview.columns.map((c) => (
                    <th key={c.name} className="border-b border-forge-border px-2 py-1 text-left">
                      {c.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.slice(0, 20).map((row, i) => (
                  <tr key={i}>
                    {preview.columns.map((c) => (
                      <td key={c.name} className="border-b border-forge-border/50 px-2 py-1">
                        {String(row[c.name] ?? "")}
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
