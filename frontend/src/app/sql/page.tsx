"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Play, Save } from "lucide-react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

export default function SqlStudioPage() {
  const [datasetId, setDatasetId] = useState("");
  const [sql, setSql] = useState("SELECT * FROM dataset LIMIT 100");
  const [saveName, setSaveName] = useState("");

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });

  const { data: schema } = useQuery({
    queryKey: ["sql-schema", datasetId],
    queryFn: () => api.sqlStudioSchema(datasetId),
    enabled: !!datasetId,
  });

  const { data: history = [] } = useQuery({
    queryKey: ["sql-history"],
    queryFn: () => api.sqlQueryHistory(),
  });

  const { data: saved = [] } = useQuery({
    queryKey: ["sql-saved"],
    queryFn: () => api.listSavedQueries(),
  });

  const execute = useMutation({
    mutationFn: () => api.sqlStudioExecute(datasetId, sql),
  });

  return (
    <div className="flex gap-4">
      <aside className="hidden w-56 shrink-0 lg:block">
        <Card title="Tables">
          {schema ? (
            <ul className="text-xs text-forge-muted">
              <li className="font-medium text-forge-text">dataset</li>
              {schema.columns.map((c) => (
                <li key={c.name} className="ml-2">
                  {c.name} <span className="opacity-60">({c.dtype})</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs">Select a dataset</p>
          )}
        </Card>
        <Card title="Saved" className="mt-4">
          <ul className="max-h-40 overflow-auto text-xs">
            {saved.map((q) => (
              <li key={q.id}>
                <button
                  type="button"
                  className="w-full py-1 text-left hover:text-forge-text"
                  onClick={() => {
                    setSql(q.sql_text);
                    if (q.dataset_id) setDatasetId(q.dataset_id);
                  }}
                >
                  {q.name}
                </button>
              </li>
            ))}
          </ul>
        </Card>
      </aside>

      <div className="min-w-0 flex-1">
        <h1 className="mb-4 text-2xl font-bold text-forge-text">SQL Studio</h1>
        <div className="mb-4 flex flex-wrap gap-2">
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm text-forge-text"
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
          >
            <option value="">Dataset…</option>
            {datasets.filter((d) => d.status === "ready").map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <Button
            disabled={!datasetId}
            loading={execute.isPending}
            onClick={() => execute.mutate()}
          >
            <Play className="h-4 w-4" /> Run
          </Button>
          <input
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            placeholder="Save as…"
            value={saveName}
            onChange={(e) => setSaveName(e.target.value)}
          />
          <Button
            variant="secondary"
            disabled={!saveName || !datasetId}
            onClick={() =>
              api.saveSqlQuery({ name: saveName, dataset_id: datasetId, sql_text: sql })
            }
          >
            <Save className="h-4 w-4" /> Save
          </Button>
        </div>

        <div className="mb-4 overflow-hidden rounded-lg border border-forge-border">
          <MonacoEditor
            height="220px"
            language="sql"
            theme="vs-dark"
            value={sql}
            onChange={(v) => setSql(v ?? "")}
            options={{ minimap: { enabled: false }, fontSize: 13 }}
          />
        </div>

        {execute.data && execute.data.rows.length > 0 && execute.data.columns.length >= 2 && (
          <Card title="Chart preview" className="mb-4">
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={execute.data.rows.slice(0, 24).map((row) => ({
                    name: String(row[execute.data!.columns[0]] ?? ""),
                    value: Number(row[execute.data!.columns[1]] ?? 0),
                  }))}
                >
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="var(--forge-primary-bg)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        )}

        {execute.data && (
          <Card title={`Results · ${execute.data.runtime_ms}ms · ${execute.data.total_rows} rows`}>
            <div className="max-h-96 overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    {execute.data.columns.map((c) => (
                      <th key={c} className="border-b border-forge-border px-2 py-1 text-left">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {execute.data.rows.map((row, i) => (
                    <tr key={i}>
                      {execute.data!.columns.map((c) => (
                        <td key={c} className="px-2 py-1 text-forge-muted">
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

        {execute.isError && (
          <p className="mt-2 text-sm text-red-500">{(execute.error as Error).message}</p>
        )}

        <Card title="Query history" className="mt-6">
          <ul className="max-h-48 space-y-2 overflow-auto text-xs text-forge-muted">
            {history.slice(0, 20).map((h) => (
              <li key={h.id}>
                <button
                  type="button"
                  className="text-left hover:text-forge-text"
                  onClick={() => {
                    setSql(h.sql_text);
                    if (h.dataset_id) setDatasetId(h.dataset_id);
                  }}
                >
                  {h.success ? "✓" : "✗"} {h.runtime_ms}ms — {h.sql_text.slice(0, 80)}…
                </button>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
