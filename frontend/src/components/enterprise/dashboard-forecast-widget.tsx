"use client";

import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, type DatasetSummary, type FilterCondition } from "@/lib/api";
import { Button } from "@/components/ui/button";

type Props = {
  dataset: DatasetSummary;
  settings: Record<string, unknown>;
  extraFilters: FilterCondition[];
  liveRefresh?: boolean;
};

export function DashboardForecastWidget({ dataset, settings, extraFilters, liveRefresh }: Props) {
  const dateCol = String(settings.date_column ?? "date");
  const valueCol = String(settings.value_column ?? "revenue");
  const method = String(settings.method ?? "linear");
  const horizon = Number(settings.horizon_days ?? 14);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["dash-forecast", dataset.id, dateCol, valueCol, method, horizon, extraFilters],
    queryFn: () =>
      api.forecast(dataset.id, {
        date_column: dateCol,
        value_column: valueCol,
        horizon_days: horizon,
        method,
        extra_filters: extraFilters,
      }),
    enabled: !!dataset.id,
    refetchInterval: liveRefresh ? 8000 : false,
  });

  if (isLoading) {
    return <p className="p-4 text-xs text-forge-muted">Loading forecast…</p>;
  }
  if (isError) {
    return (
      <p className="p-4 text-xs text-red-400">
        {error instanceof Error ? error.message : "Forecast failed"}
      </p>
    );
  }
  if (!data?.points?.length) {
    return <p className="p-4 text-xs text-forge-muted">No forecast data for current filters.</p>;
  }

  const chartData = data.points.map((p) => ({
    name: p.date,
    value: p.value,
    forecast: p.is_forecast,
  }));

  return (
    <div className="flex h-full flex-col p-2">
      <div className="mb-1 flex items-center justify-between">
        <p className="text-[10px] text-forge-muted">{data.summary}</p>
        <Button
          variant="ghost"
          className="h-7 px-2 text-[10px]"
          onClick={async () => {
            const blob = await api.forecastExportCsv(dataset.id, {
              date_column: dateCol,
              value_column: valueCol,
              horizon_days: horizon,
              method,
              extra_filters: extraFilters,
            });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `forecast-${dataset.name}.csv`;
            a.click();
          }}
        >
          <Download className="h-3 w-3" /> CSV
        </Button>
      </div>
      <div className="min-h-[120px] flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <XAxis dataKey="name" tick={{ fontSize: 9 }} />
            <YAxis tick={{ fontSize: 9 }} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="var(--forge-text)" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
