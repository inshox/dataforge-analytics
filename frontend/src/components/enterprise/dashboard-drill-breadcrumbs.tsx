"use client";

import { useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

const DEMO_CHAIN: Record<string, { label: string; parent?: string }> = {
  "00000000-0000-4000-8000-000000000002": { label: "Executive" },
  "00000000-0000-4000-8000-000000000003": {
    label: "Regional",
    parent: "00000000-0000-4000-8000-000000000002",
  },
  "00000000-0000-4000-8000-000000000004": {
    label: "Customer",
    parent: "00000000-0000-4000-8000-000000000003",
  },
};

export function DashboardDrillBreadcrumbs({ dashboardId }: { dashboardId: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: dashboards = [] } = useQuery({
    queryKey: ["dashboards"],
    queryFn: () => api.listDashboards(),
  });

  const trail = useMemo(() => {
    const crumbs: { id: string; label: string }[] = [];
    let cur: string | undefined = dashboardId;
    const byId: Record<string, string> = Object.fromEntries(dashboards.map((d) => [d.id, d.name]));
    while (cur) {
      const meta: { label: string; parent?: string } | undefined = DEMO_CHAIN[cur];
      crumbs.unshift({
        id: cur,
        label: meta?.label ?? byId[cur] ?? "Dashboard",
      });
      cur = meta?.parent;
    }
    if (crumbs.length <= 1 && dashboards.length) {
      const self = dashboards.find((d) => d.id === dashboardId);
      if (self) return [{ id: dashboardId, label: self.name }];
    }
    return crumbs;
  }, [dashboardId, dashboards]);

  const parent = DEMO_CHAIN[dashboardId]?.parent;
  const backHref = parent
    ? `/dashboards/view?${new URLSearchParams({ id: parent, ...Object.fromEntries(searchParams.entries()) }).toString()}`
    : null;

  if (trail.length <= 1 && !backHref) return null;

  return (
    <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
      {backHref && (
        <Button variant="secondary" onClick={() => router.push(backHref)}>
          <ChevronLeft className="h-4 w-4" /> Back
        </Button>
      )}
      <nav className="flex flex-wrap items-center gap-1 text-forge-muted">
        {trail.map((c, i) => (
          <span key={c.id} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="h-3 w-3" />}
            <button
              type="button"
              className={
                c.id === dashboardId
                  ? "font-medium text-forge-text"
                  : "hover:text-forge-text"
              }
              onClick={() => {
                const p = new URLSearchParams(searchParams.toString());
                p.set("id", c.id);
                router.push(`/dashboards/view?${p.toString()}`);
              }}
            >
              {c.label}
            </button>
          </span>
        ))}
      </nav>
    </div>
  );
}
