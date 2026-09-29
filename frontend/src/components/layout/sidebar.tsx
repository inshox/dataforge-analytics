"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { datasetHref, type DatasetTab } from "@/lib/navigation";
import {
  Database,
  FileText,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeft,
  Settings,
  BarChart3,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/app-store";

const nav = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/dashboards", label: "Dashboards", icon: BarChart3 },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/chart-studio", label: "Chart Studio", icon: BarChart3 },
  { href: "/sql", label: "SQL Studio", icon: FileText },
  { href: "/transform", label: "Transform", icon: FileText },
  { href: "/relationships", label: "Relationships", icon: Database },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const toggle = useAppStore((s) => s.toggleSidebar);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-forge-border bg-forge-surface transition-all duration-300",
        collapsed ? "w-[72px]" : "w-64"
      )}
    >
      <div className="flex h-16 items-center gap-3 border-b border-forge-border px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-forge-border bg-forge-card">
          <BarChart3 className="h-5 w-5 text-forge-text" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-sm font-semibold text-forge-text">DataForge</p>
            <p className="text-xs text-forge-muted">Analytics</p>
          </div>
        )}
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-forge-accent-soft font-medium text-forge-text"
                  : "text-forge-muted hover:bg-forge-hover hover:text-forge-text"
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-forge-border p-3">
        <button
          type="button"
          onClick={toggle}
          className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-forge-muted hover:bg-forge-hover"
        >
          {collapsed ? <PanelLeft className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}

function DatasetSubNavInner({ datasetId }: { datasetId: string }) {
  const searchParams = useSearchParams();
  const activeTab = (searchParams.get("tab") as DatasetTab) || "overview";
  const items: { tab: DatasetTab; label: string }[] = [
    { tab: "overview", label: "Overview" },
    { tab: "table", label: "Table" },
    { tab: "analysis", label: "Analysis" },
    { tab: "charts", label: "Charts" },
    { tab: "sql", label: "SQL Lab" },
    { tab: "analyst", label: "AI Analyst" },
  ];

  return (
    <div className="mb-6 flex flex-wrap gap-2">
      {items.map(({ tab, label }) => (
        <Link
          key={tab}
          href={datasetHref(datasetId, tab)}
          className={cn(
            "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
            activeTab === tab
              ? "bg-forge-accent-soft text-forge-text"
              : "bg-forge-hover text-forge-muted hover:text-forge-text"
          )}
        >
          {label}
        </Link>
      ))}
    </div>
  );
}

export function DatasetSubNav({ datasetId }: { datasetId: string }) {
  return (
    <Suspense fallback={<div className="mb-6 h-10 animate-pulse rounded-lg bg-forge-hover" />}>
      <DatasetSubNavInner datasetId={datasetId} />
    </Suspense>
  );
}
