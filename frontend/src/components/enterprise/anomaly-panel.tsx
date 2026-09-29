"use client";

import { useMutation } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function AnomalyPanel({ datasetId }: { datasetId: string }) {
  const { data, mutate, isPending } = useMutation({
    mutationFn: () => api.detectAnomalies(datasetId),
  });

  return (
    <Card title="Anomaly detection">
      <p className="mb-3 text-sm text-forge-muted">
        IQR, z-score, and rolling deviation heuristics — fully local.
      </p>
      <Button loading={isPending} onClick={() => mutate()}>
        <AlertTriangle className="h-4 w-4" /> Scan for anomalies
      </Button>
      {data && (
        <div className="mt-4">
          <p className="mb-2 text-sm text-forge-text">{data.summary}</p>
          <ul className="space-y-2">
            {data.anomalies.map((a, i) => (
              <li
                key={`${a.column}-${i}`}
                className="rounded-lg border border-forge-border bg-forge-hover px-3 py-2 text-sm text-forge-text"
              >
                <span
                  className={`mr-2 rounded px-1.5 py-0.5 text-[10px] uppercase ${
                    a.severity === "high"
                      ? "bg-red-500/20 text-red-400"
                      : a.severity === "medium"
                        ? "bg-amber-500/20 text-amber-600 dark:text-amber-300"
                        : "bg-forge-accent-soft text-forge-muted"
                  }`}
                >
                  {a.severity}
                </span>
                <strong>{a.column}</strong> — {a.explanation}
              </li>
            ))}
            {data.anomalies.length === 0 && (
              <li className="text-sm text-forge-muted">No significant anomalies detected.</li>
            )}
          </ul>
        </div>
      )}
    </Card>
  );
}
