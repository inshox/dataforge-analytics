"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Database, Rows3, Upload, Inbox } from "lucide-react";
import { api } from "@/lib/api";
import { datasetHref } from "@/lib/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DashboardSkeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { formatBytes, formatNumber } from "@/lib/utils";
import { useBackendStatus } from "@/hooks/use-backend-status";

export default function DashboardPage() {
  const router = useRouter();
  const { state: backendState } = useBackendStatus();
  const { data: datasets = [], isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
    enabled: backendState === "online",
  });

  const totalRows = datasets.reduce((a, d) => a + d.row_count, 0);
  const ready = datasets.filter((d) => d.status === "ready").length;
  const demo = datasets.find((d) => d.tags.includes("demo"));

  if (backendState === "starting" || (isLoading && backendState === "online")) {
    return <DashboardSkeleton />;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-forge-text">Dashboard</h1>
        <p className="mt-1 text-forge-muted">
          Analyze large datasets locally — fast imports, filters, and charts.
        </p>
      </div>

      {demo && (
        <Card className="mb-6 border-forge-border bg-forge-accent-soft">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-forge-text">Dataset demo</p>
              <p className="text-xs text-forge-muted">
                Przykładowe dane sprzedaży — tabela, filtry, wykresy i SQL Lab.
              </p>
            </div>
            <Button onClick={() => router.push(datasetHref(demo.id, "table"))}>Otwórz demo</Button>
          </div>
        </Card>
      )}

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className="flex items-center gap-3">
            <Database className="h-8 w-8 text-forge-muted" />
            <div>
              <p className="text-2xl font-bold tabular-nums text-forge-text">{datasets.length}</p>
              <p className="text-xs text-forge-muted">Datasets</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <Rows3 className="h-8 w-8 text-forge-muted" />
            <div>
              <p className="text-2xl font-bold tabular-nums text-forge-text">{formatNumber(totalRows)}</p>
              <p className="text-xs text-forge-muted">Total rows</p>
            </div>
          </div>
        </Card>
        <Card>
          <p className="text-2xl font-bold tabular-nums text-forge-text">{ready}</p>
          <p className="text-xs text-forge-muted">Ready for analysis</p>
        </Card>
        <Card>
          <Link href="/datasets">
            <Button className="w-full">
              <Upload className="h-4 w-4" /> Import data
            </Button>
          </Link>
        </Card>
      </div>

      <Card title="Recent datasets">
        {backendState === "offline" ? (
          <EmptyState
            icon={Inbox}
            title="Backend not connected"
            description="Wait for the analytics engine to start, or open Settings → Retry connection."
          />
        ) : datasets.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No datasets yet"
            description="Import a CSV file to create your first dataset and start exploring."
            action={
              <Link href="/datasets">
                <Button>Go to import</Button>
              </Link>
            }
          />
        ) : (
          <ul className="divide-y divide-forge-border">
            {datasets.slice(0, 5).map((d) => (
              <li key={d.id} className="flex items-center justify-between py-3">
                <div>
                  <button
                    type="button"
                    className="font-medium text-forge-text hover:underline"
                    onClick={() => router.push(datasetHref(d.id))}
                  >
                    {d.name}
                  </button>
                  <p className="text-xs text-forge-muted">
                    {formatNumber(d.row_count)} rows · {d.column_count} cols · {formatBytes(d.file_size_bytes)}
                  </p>
                </div>
                <span className="rounded-full bg-forge-success-bg px-2 py-0.5 text-xs font-medium text-forge-success-fg">
                  {d.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
