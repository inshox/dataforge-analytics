"use client";

import { useMutation } from "@tanstack/react-query";
import { Copy, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function InsightsPanel({ datasetId }: { datasetId: string }) {
  const { data, mutate, isPending } = useMutation({
    mutationFn: () => api.generateInsights(datasetId),
  });

  const copyAll = () => {
    if (!data?.insights.length) return;
    const text = data.insights.map((i) => `• [${i.severity}] ${i.message}`).join("\n");
    void navigator.clipboard.writeText(text);
  };

  return (
    <Card title="AI Insights">
      <p className="mb-3 text-sm text-forge-muted">
        Automatic business insights from your data — 100% local, no cloud AI.
      </p>
      <div className="mb-4 flex gap-2">
        <Button loading={isPending} onClick={() => mutate()}>
          <Sparkles className="h-4 w-4" /> Generate insights
        </Button>
        {data && (
          <Button variant="secondary" onClick={copyAll}>
            <Copy className="h-4 w-4" /> Copy
          </Button>
        )}
      </div>
      {data && (
        <ul className="space-y-2">
          {data.insights.map((ins) => (
            <li
              key={ins.id}
              className="rounded-lg border border-forge-border bg-forge-hover px-3 py-2 text-sm text-forge-text"
            >
              <span
                className={`mr-2 rounded px-1.5 py-0.5 text-[10px] uppercase ${
                  ins.severity === "high"
                    ? "bg-red-500/20 text-red-400"
                    : ins.severity === "medium"
                      ? "bg-amber-500/20 text-amber-600 dark:text-amber-300"
                      : "bg-forge-accent-soft text-forge-muted"
                }`}
              >
                {ins.severity}
              </span>
              {ins.message}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
