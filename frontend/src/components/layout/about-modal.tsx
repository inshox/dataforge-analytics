"use client";

import { APP_VERSION } from "@/lib/desktop";
import { Button } from "@/components/ui/button";

export function AboutModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="glass-panel max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="about-title"
      >
        <h2 id="about-title" className="text-lg font-semibold text-forge-text">
          DataForge Analytics
        </h2>
        <p className="mt-1 text-sm text-forge-muted">Version {APP_VERSION}</p>
        <p className="mt-4 text-sm leading-relaxed text-forge-muted">
          Premium local data analytics for large files. Import CSV, Excel, Parquet, and JSON;
          profile, filter, chart, and query with DuckDB — all on your machine.
        </p>
        <ul className="mt-4 space-y-1 text-xs text-forge-muted">
          <li>Polars + DuckDB engine</li>
          <li>AI Analyst (local heuristics)</li>
          <li>PDF/HTML reports</li>
        </ul>
        <div className="mt-6 flex justify-end">
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>
  );
}
