"use client";

import { useParams } from "next/navigation";
import { DashboardEditor } from "@/components/enterprise/dashboard-editor";

export default function DashboardIdPage() {
  const params = useParams();
  const raw = params.id as string;
  if (raw === "placeholder") {
    return <p className="text-forge-muted">Open a dashboard from the list.</p>;
  }
  return <DashboardEditor dashboardId={raw} />;
}
