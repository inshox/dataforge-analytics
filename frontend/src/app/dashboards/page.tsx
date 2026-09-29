"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Copy, LayoutDashboard, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

export default function DashboardsListPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const { data: dashboards = [], isLoading } = useQuery({
    queryKey: ["dashboards"],
    queryFn: () => api.listDashboards(),
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["dashboard-templates"],
    queryFn: () => api.listDashboardTemplates(),
  });
  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
  });

  const create = useMutation({
    mutationFn: () => api.createDashboard(`Dashboard ${new Date().toLocaleDateString()}`),
    onSuccess: (d) => {
      void qc.invalidateQueries({ queryKey: ["dashboards"] });
      router.push(`/dashboards/view?id=${d.id}`);
    },
  });

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-forge-text">Dashboards</h1>
          <p className="text-sm text-forge-muted">Build drag-and-drop BI dashboards from your datasets.</p>
        </div>
        <Button onClick={() => create.mutate()} loading={create.isPending}>
          <Plus className="h-4 w-4" /> Create dashboard
        </Button>
      </div>

      {templates.length > 0 && (
        <Card title="Dashboard templates" className="mb-6">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                className="rounded-lg border border-forge-border bg-forge-hover p-4 text-left transition hover:border-forge-text/30"
                onClick={async () => {
                  const ds = datasets.find((d) => d.status === "ready");
                  if (!ds) return;
                  const d = await api.instantiateDashboardTemplate(t.id, ds.id);
                  void qc.invalidateQueries({ queryKey: ["dashboards"] });
                  router.push(`/dashboards/view?id=${d.id}`);
                }}
              >
                <p className="font-medium text-forge-text">{t.name}</p>
                <p className="mt-1 text-xs text-forge-muted">{t.description}</p>
                <p className="mt-2 text-[10px] uppercase text-forge-muted">
                  {t.category} · {t.widget_count} widgets
                </p>
              </button>
            ))}
          </div>
        </Card>
      )}

      {isLoading ? (
        <p className="text-forge-muted">Loading…</p>
      ) : dashboards.length === 0 ? (
        <EmptyState
          icon={LayoutDashboard}
          title="No dashboards yet"
          description="Create your first dashboard and add KPI cards and charts."
          action={<Button onClick={() => create.mutate()}>Create dashboard</Button>}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {dashboards.map((d) => (
            <Card key={d.id}>
              <Link href={`/dashboards/view?id=${d.id}`} className="block">
                <h3 className="font-semibold text-forge-text hover:underline">{d.name}</h3>
                <p className="mt-1 text-xs text-forge-muted">{d.widget_count} widgets</p>
              </Link>
              <div className="mt-4 flex gap-2">
                <Button
                  variant="ghost"
                  className="h-8 px-2"
                  onClick={async () => {
                    const dup = await api.duplicateDashboard(d.id);
                    void qc.invalidateQueries({ queryKey: ["dashboards"] });
                    router.push(`/dashboards/view?id=${dup.id}`);
                  }}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  className="h-8 px-2"
                  onClick={async () => {
                    if (!confirm("Delete this dashboard?")) return;
                    await api.deleteDashboard(d.id);
                    void qc.invalidateQueries({ queryKey: ["dashboards"] });
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
