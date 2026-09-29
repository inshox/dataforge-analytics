"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";

export function WorkersPanel() {
  const { data: stats } = useQuery({
    queryKey: ["worker-stats"],
    queryFn: () => api.workerStats(),
    refetchInterval: 2000,
  });

  const { data: jobs = [] } = useQuery({
    queryKey: ["worker-jobs"],
    queryFn: () => api.listWorkers(),
    refetchInterval: 2000,
  });

  return (
    <Card title="Background workers" className="mb-4">
      <p className="mb-3 text-sm text-forge-muted">
        Import, export, profiling, and forecasting run off the UI thread.
      </p>
      <dl className="mb-4 grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
        <div>
          <dt className="text-forge-muted">Active</dt>
          <dd className="font-semibold text-forge-text">{stats?.active_jobs ?? 0}</dd>
        </div>
        <div>
          <dt className="text-forge-muted">Queued</dt>
          <dd className="font-semibold text-forge-text">{stats?.queued_jobs ?? 0}</dd>
        </div>
        <div>
          <dt className="text-forge-muted">Memory</dt>
          <dd className="font-semibold text-forge-text">
            {stats?.memory_mb != null ? `${stats.memory_mb} MB` : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-forge-muted">CPU</dt>
          <dd className="font-semibold text-forge-text">
            {stats?.cpu_percent != null ? `${stats.cpu_percent}%` : "—"}
          </dd>
        </div>
      </dl>
      <ul className="max-h-48 space-y-2 overflow-auto text-xs">
        {jobs.map((j) => (
          <li
            key={j.id}
            className="flex items-center justify-between rounded-lg border border-forge-border px-3 py-2"
          >
            <span className="text-forge-text">
              {j.job_type} · {j.status}
            </span>
            <span className="tabular-nums text-forge-muted">{j.progress}%</span>
          </li>
        ))}
        {jobs.length === 0 && <li className="text-forge-muted">No recent jobs</li>}
      </ul>
    </Card>
  );
}
