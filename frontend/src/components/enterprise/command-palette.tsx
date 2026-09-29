"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { datasetHref } from "@/lib/navigation";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const router = useRouter();
  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.listDatasets(),
    enabled: open,
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!open) return null;

  const routes = [
    { label: "Home", href: "/dashboard" },
    { label: "Dashboards", href: "/dashboards" },
    { label: "Datasets", href: "/datasets" },
    { label: "Chart Studio", href: "/chart-studio" },
    { label: "SQL Studio", href: "/sql" },
    { label: "Relationships", href: "/relationships" },
    { label: "Reports", href: "/reports" },
    { label: "Settings", href: "/settings" },
  ];

  const filtered = datasets.filter((d) => !q || d.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div
      className="fixed inset-0 z-[200] flex items-start justify-center bg-black/50 pt-[15vh] p-4"
      onClick={() => setOpen(false)}
    >
      <div
        className="glass-panel w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          autoFocus
          className="w-full border-b border-forge-border bg-transparent px-4 py-3 text-forge-text outline-none"
          placeholder="Search datasets or jump to… (Ctrl+K)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="max-h-80 overflow-auto p-2">
          <p className="px-2 py-1 text-xs font-medium text-forge-muted">Pages</p>
          {routes.map((r) => (
            <button
              key={r.href}
              type="button"
              className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-forge-hover"
              onClick={() => {
                router.push(r.href);
                setOpen(false);
              }}
            >
              {r.label}
            </button>
          ))}
          {filtered.length > 0 && (
            <>
              <p className="mt-2 px-2 py-1 text-xs font-medium text-forge-muted">Datasets</p>
              {filtered.slice(0, 8).map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-forge-hover"
                  onClick={() => {
                    router.push(datasetHref(d.id));
                    setOpen(false);
                  }}
                >
                  {d.name}
                </button>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
