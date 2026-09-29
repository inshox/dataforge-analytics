"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type DatasetSummary, type FilterCondition } from "@/lib/api";

type Props = {
  dataset: DatasetSummary;
  extraFilters: FilterCondition[];
  liveRefresh?: boolean;
};

export function DashboardAnomalyWidget({ dataset, extraFilters, liveRefresh }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["dash-anomaly", dataset.id, extraFilters],
    queryFn: () => api.detectAnomalies(dataset.id, extraFilters),
    enabled: !!dataset.id,
    refetchInterval: liveRefresh ? 10000 : false,
  });

  if (isLoading) {
    return <p className="p-4 text-xs text-forge-muted">Scanning for anomalies…</p>;
  }
  if (isError) {
    return <p className="p-4 text-xs text-red-400">Anomaly detection failed.</p>;
  }

  const items = data?.anomalies ?? [];
  if (!items.length) {
    return <p className="p-4 text-xs text-forge-muted">{data?.summary ?? "No anomalies."}</p>;
  }

  return (
    <div className="h-full overflow-y-auto p-2">
      <p className="mb-2 text-[10px] text-forge-muted">{data?.summary}</p>
      <ul className="space-y-1">
        {items.slice(0, 8).map((a, i) => (
          <li
            key={`${a.column}-${i}`}
            className="rounded border border-forge-border bg-forge-hover px-2 py-1 text-[10px]"
          >
            <span className="font-medium text-forge-text">{a.column}</span>
            <span className="ml-1 text-forge-muted">· {a.severity}</span>
            <p className="text-forge-muted">{a.explanation}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
