"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { Download, TrendingUp } from "lucide-react";
import { api, type DatasetSummary } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const HORIZONS = [30, 90, 180, 365] as const;
const METHODS = [
  { id: "linear", label: "Linear" },
  { id: "exponential", label: "Exponential" },
  { id: "holt_winters", label: "Holt-Winters (seasonal)" },
  { id: "arima", label: "ARIMA" },
  { id: "prophet", label: "Prophet (optional)" },
] as const;

export function ForecastPanel({ dataset }: { dataset: DatasetSummary }) {
  const dateCols = dataset.columns.filter((c) => /date|time|day|month|year/i.test(c.name));
  const numCols = dataset.columns.filter((c) =>
    /int|float|decimal|numeric|number/i.test(c.dtype)
  );
  const [dateColumn, setDateColumn] = useState(dateCols[0]?.name ?? dataset.columns[0]?.name ?? "");
  const [valueColumn, setValueColumn] = useState(
    numCols[0]?.name ?? dataset.columns[1]?.name ?? ""
  );
  const [horizon, setHorizon] = useState<number>(90);
  const [method, setMethod] = useState("holt_winters");
  const [confidence, setConfidence] = useState(0.95);

  const { data, mutate, isPending } = useMutation({
    mutationFn: () =>
      api.forecast(dataset.id, {
        date_column: dateColumn,
        value_column: valueColumn,
        horizon_days: horizon,
        method,
        confidence_level: confidence,
      }),
  });

  const chartData =
    data?.points.map((p) => ({
      date: p.date.slice(0, 10),
      value: p.value,
      lower: p.lower ?? undefined,
      upper: p.upper ?? undefined,
      forecast: p.is_forecast,
    })) ?? [];

  const exportCsv = () => {
    if (!data?.prediction_table?.length) return;
    const header = "date,value,lower,upper,is_forecast\n";
    const rows = data.prediction_table
      .map(
        (r) =>
          `${r.date},${r.value},${r.lower ?? ""},${r.upper ?? ""},${r.is_forecast}`
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `forecast-${dataset.name}.csv`;
    a.click();
  };

  return (
    <Card title="Forecast 2.0">
      <p className="mb-3 text-sm text-forge-muted">
        Linear, exponential, Holt-Winters, ARIMA, and optional Prophet — fully local.
      </p>
      <div className="mb-4 flex flex-wrap gap-2">
        <select
          className="rounded-lg border border-forge-border bg-forge-surface px-2 py-1 text-sm text-forge-text"
          value={dateColumn}
          onChange={(e) => setDateColumn(e.target.value)}
        >
          {dataset.columns.map((c) => (
            <option key={c.name} value={c.name}>
              Date: {c.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-forge-border bg-forge-surface px-2 py-1 text-sm text-forge-text"
          value={valueColumn}
          onChange={(e) => setValueColumn(e.target.value)}
        >
          {dataset.columns.map((c) => (
            <option key={c.name} value={c.name}>
              Value: {c.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-forge-border bg-forge-surface px-2 py-1 text-sm text-forge-text"
          value={method}
          onChange={(e) => setMethod(e.target.value)}
        >
          {METHODS.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-forge-border bg-forge-surface px-2 py-1 text-sm text-forge-text"
          value={horizon}
          onChange={(e) => setHorizon(Number(e.target.value))}
        >
          {HORIZONS.map((d) => (
            <option key={d} value={d}>
              {d} days
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-xs text-forge-muted">
          Confidence {(confidence * 100).toFixed(0)}%
          <input
            type="range"
            min={80}
            max={99}
            value={confidence * 100}
            onChange={(e) => setConfidence(Number(e.target.value) / 100)}
          />
        </label>
        <Button loading={isPending} onClick={() => mutate()}>
          <TrendingUp className="h-4 w-4" /> Run
        </Button>
        {data && (
          <Button variant="secondary" onClick={exportCsv}>
            <Download className="h-4 w-4" /> CSV
          </Button>
        )}
      </div>
      {data && (
        <>
          <p className="mb-2 text-sm text-forge-text">
            {data.summary}
            {data.seasonality_detected ? " · Seasonality detected" : ""}
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--forge-border)" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="upper"
                  stroke="var(--forge-muted)"
                  strokeDasharray="4 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="lower"
                  stroke="var(--forge-muted)"
                  strokeDasharray="4 4"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="var(--forge-primary-bg)"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </Card>
  );
}
