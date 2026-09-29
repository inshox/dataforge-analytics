"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X } from "lucide-react";
import { useTabStore } from "@/store/tab-store";
import { cn } from "@/lib/utils";
import { useEffect } from "react";

export function WorkspaceTabs() {
  const pathname = usePathname();
  const { tabs, activeId, openTab, closeTab, setActive } = useTabStore();

  useEffect(() => {
    const label =
      pathname.startsWith("/datasets")
        ? "Datasets"
        : pathname.startsWith("/dashboards")
          ? "Dashboards"
          : pathname.startsWith("/sql")
            ? "SQL Studio"
            : pathname.startsWith("/chart-studio")
              ? "Chart Studio"
              : "Page";
    openTab({ id: pathname, label, href: pathname });
  }, [pathname, openTab]);

  return (
    <div className="mb-4 flex items-center gap-1 overflow-x-auto border-b border-forge-border pb-1">
      {tabs.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-center gap-1 rounded-t-lg border border-b-0 border-forge-border px-3 py-1.5 text-xs transition-colors",
            activeId === t.id || pathname === t.href
              ? "bg-forge-surface text-forge-text"
              : "bg-transparent text-forge-muted hover:bg-forge-hover"
          )}
        >
          <Link href={t.href} onClick={() => setActive(t.id)} className="max-w-[140px] truncate">
            {t.label}
          </Link>
          {t.id !== "home" && (
            <button
              type="button"
              className="rounded p-0.5 hover:bg-forge-hover"
              onClick={() => closeTab(t.id)}
              aria-label="Close tab"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
