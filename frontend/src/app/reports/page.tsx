"use client";

import { useQuery } from "@tanstack/react-query";
import { FileDown, FileText } from "lucide-react";
import { api, getApiBase } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useBackendStatus } from "@/hooks/use-backend-status";
import { EmptyState } from "@/components/ui/empty-state";
import { Inbox } from "lucide-react";

async function downloadReport(datasetId: string, name: string, format: "html" | "pdf") {
  const url = `${getApiBase()}/datasets/${datasetId}/report?format=${format}`;
  const res = await fetch(url, {
    headers: { Authorization: "Bearer demo-token" },
  });
  if (!res.ok) throw new Error("Report generation failed");
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${name}-report.${format === "pdf" ? "pdf" : "html"}`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function ReportsPage() {
  const { state } = useBackendStatus();
  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
    enabled: state === "online",
  });
  const ready = datasets.filter((d) => d.status === "ready");

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-forge-text">Reports</h1>
      <p className="mb-6 text-sm text-forge-muted">
        Generate PDF or HTML reports with summary stats, profiling insights, and charts.
      </p>

      {ready.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title="No datasets ready"
          description="Import and finalize a dataset to generate reports."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {ready.map((d) => (
            <Card key={d.id} title={d.name}>
              <p className="mb-4 text-xs text-forge-muted">
                {d.row_count.toLocaleString()} rows · {d.column_count} columns
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="secondary"
                  onClick={() => void downloadReport(d.id, d.name, "html").catch(alert)}
                >
                  <FileText className="h-4 w-4" /> HTML report
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => void downloadReport(d.id, d.name, "pdf").catch(alert)}
                >
                  <FileDown className="h-4 w-4" /> PDF report
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
