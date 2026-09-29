"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { api } from "@/lib/api";
import { ChartPanel } from "@/components/charts/chart-panel";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const CHART_TYPES = ["bar", "line", "area", "pie", "scatter", "histogram", "heatmap", "boxplot", "treemap"];

export default function ChartStudioPage() {
  const [datasetId, setDatasetId] = useState("");
  const [templateName, setTemplateName] = useState("");
  const qc = useQueryClient();

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });

  const dataset = datasets.find((d) => d.id === datasetId);

  const saveTemplate = useMutation({
    mutationFn: () =>
      api.saveChartTemplate({
        name: templateName || "Untitled chart",
        dataset_id: datasetId,
        chart_type: "bar",
        config: { saved_from: "chart-studio" },
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["chart-templates"] });
      setTemplateName("");
    },
  });

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-forge-text">Chart Studio</h1>
      <p className="mb-6 text-sm text-forge-muted">
        Design charts and save templates — export from the chart preview (PNG via browser).
      </p>

      <Card className="mb-6">
        <label className="mb-2 block text-sm text-forge-muted">Dataset</label>
        <select
          className="w-full max-w-md rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm text-forge-text"
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
        >
          <option value="">Select dataset…</option>
          {datasets.filter((d) => d.status === "ready").map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-forge-muted">Supported types: {CHART_TYPES.join(", ")}</p>
      </Card>

      {dataset && (
        <>
          <ChartPanel dataset={dataset} />
          <Card title="Save template" className="mt-6">
            <div className="flex flex-wrap gap-2">
              <input
                className="rounded-lg border border-forge-border bg-forge-surface px-3 py-2 text-sm text-forge-text"
                placeholder="Template name"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
              />
              <Button loading={saveTemplate.isPending} onClick={() => saveTemplate.mutate()}>
                <Save className="h-4 w-4" /> Save template
              </Button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
