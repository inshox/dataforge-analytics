"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardFilterProvider } from "@/contexts/dashboard-filter-context";
import { DashboardEditor } from "@/components/enterprise/dashboard-editor";

function DashboardViewInner() {
  const sp = useSearchParams();
  const id = sp.get("id")?.trim();
  if (!id) {
    return <p className="text-forge-muted">Missing dashboard id.</p>;
  }
  return (
    <DashboardFilterProvider dashboardId={id}>
      <DashboardEditor dashboardId={id} />
    </DashboardFilterProvider>
  );
}

export default function DashboardViewPage() {
  return (
    <Suspense fallback={<p className="text-forge-muted">Loading…</p>}>
      <DashboardViewInner />
    </Suspense>
  );
}
