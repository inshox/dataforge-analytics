"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { GitBranch, Wand2 } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function RelationshipsPage() {
  const qc = useQueryClient();
  const [leftId, setLeftId] = useState("");
  const [rightId, setRightId] = useState("");
  const [leftCol, setLeftCol] = useState("");
  const [rightCol, setRightCol] = useState("");

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });

  const { data: rels = [], refetch } = useQuery({
    queryKey: ["relationships"],
    queryFn: () => api.listRelationships(),
  });

  const { data: graph } = useQuery({
    queryKey: ["relationship-graph"],
    queryFn: () => api.relationshipGraph(),
  });

  const detect = useMutation({
    mutationFn: () => api.detectRelationships(),
    onSuccess: () => void refetch(),
  });

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-forge-text">Dataset relationships</h1>
          <p className="text-sm text-forge-muted">
            Auto-detect keys like customer_id, order_id — used by AI Analyst and dashboards.
          </p>
        </div>
        <Button loading={detect.isPending} onClick={() => detect.mutate()}>
          <Wand2 className="h-4 w-4" /> Auto-detect
        </Button>
      </div>

      <Card title="Relationship graph" className="mb-6">
        {graph && graph.nodes.length > 0 ? (
          <div className="flex flex-wrap gap-4">
            {graph.nodes.map((n) => (
              <span
                key={n.id}
                className="rounded-lg border border-forge-border bg-forge-hover px-3 py-2 text-sm text-forge-text"
              >
                {n.label}
              </span>
            ))}
            <p className="w-full text-xs text-forge-muted">{graph.edges.length} link(s)</p>
          </div>
        ) : (
          <p className="text-sm text-forge-muted">Run auto-detect or add a manual relationship.</p>
        )}
      </Card>

      <Card title="Manual relationship" className="mb-6">
        <div className="grid gap-3 md:grid-cols-2">
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            value={leftId}
            onChange={(e) => setLeftId(e.target.value)}
          >
            <option value="">Left dataset</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <input
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            placeholder="Left column"
            value={leftCol}
            onChange={(e) => setLeftCol(e.target.value)}
          />
          <select
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            value={rightId}
            onChange={(e) => setRightId(e.target.value)}
          >
            <option value="">Right dataset</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <input
            className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm"
            placeholder="Right column"
            value={rightCol}
            onChange={(e) => setRightCol(e.target.value)}
          />
        </div>
        <Button
          className="mt-3"
          onClick={async () => {
            await api.createRelationship({
              left_dataset_id: leftId,
              right_dataset_id: rightId,
              left_column: leftCol,
              right_column: rightCol,
              relationship_type: "many_to_one",
              confidence: 1,
              is_manual: true,
            });
            void refetch();
          }}
        >
          <GitBranch className="h-4 w-4" /> Create
        </Button>
      </Card>

      <Card title="Detected relationships">
        <ul className="divide-y divide-forge-border text-sm">
          {rels.map((r) => (
            <li key={r.id} className="flex flex-wrap justify-between gap-2 py-2 text-forge-text">
              <span>
                {datasets.find((d) => d.id === r.left_dataset_id)?.name ?? r.left_dataset_id}.
                <code className="text-forge-muted">{r.left_column}</code> →{" "}
                {datasets.find((d) => d.id === r.right_dataset_id)?.name ?? r.right_dataset_id}.
                <code className="text-forge-muted">{r.right_column}</code>
              </span>
              <span className="text-xs text-forge-muted">
                {(r.confidence * 100).toFixed(0)}% {r.is_manual ? "manual" : "auto"}
              </span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
