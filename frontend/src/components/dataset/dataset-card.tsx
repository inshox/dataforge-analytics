"use client";

import { useRouter } from "next/navigation";
import { datasetHref } from "@/lib/navigation";
import { formatBytes, formatNumber } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { DatasetSummary } from "@/lib/api";

export function DatasetCard({ dataset }: { dataset: DatasetSummary }) {
  const router = useRouter();

  const open = () => {
    const href = datasetHref(dataset.id);
    console.info("[DataForge] Open dataset:", dataset.id, "→", href);
    router.push(href);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      className={cn(
        "glass-panel gradient-border cursor-pointer p-5 transition",
        "hover:border-forge-border hover:shadow-lg",
        "focus:outline-none focus:ring-2 focus:ring-forge-accent/30"
      )}
      onClick={open}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          open();
        }
      }}
    >
      <h3 className="font-semibold text-forge-text">{dataset.name}</h3>
      <p className="mt-1 text-xs text-forge-muted">{dataset.source_filename}</p>
      <div className="mt-4 flex gap-4 text-sm text-forge-muted">
        <span>{formatNumber(dataset.row_count)} rows</span>
        <span>{formatBytes(dataset.file_size_bytes)}</span>
      </div>
      <span className="mt-3 inline-block rounded-full bg-forge-success-bg px-2 py-0.5 text-xs text-forge-success-fg">
        {dataset.status}
      </span>
    </div>
  );
}
