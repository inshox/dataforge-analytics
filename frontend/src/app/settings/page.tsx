"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getApiBase, getHealthCheckUrls, getServerOrigin, setApiBase, api } from "@/lib/api";
import { useAppStore } from "@/store/app-store";
import { useBackendStatus } from "@/hooks/use-backend-status";
import { APP_VERSION, getDesktopPaths, isTauri, openLogsFolder } from "@/lib/desktop";
import { WorkersPanel } from "@/components/settings/workers-panel";
import type { Theme } from "@/store/app-store";

export default function SettingsPage() {
  const theme = useAppStore((s) => s.theme);
  const setTheme = useAppStore((s) => s.setTheme);
  const [apiUrl, setApiUrl] = useState("");
  const { state, health, retry } = useBackendStatus();
  const queryClient = useQueryClient();

  const [tauri, setTauri] = useState(false);
  useEffect(() => {
    void isTauri().then(setTauri);
  }, []);

  const { data: paths } = useQuery({
    queryKey: ["desktop-paths"],
    queryFn: getDesktopPaths,
    enabled: tauri,
  });

  useEffect(() => {
    setApiUrl(getApiBase());
  }, []);

  const dataDir = health?.data_directory ?? paths?.data_directory ?? "—";
  const logFile = health?.log_file ?? paths?.log_file ?? "—";

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-forge-text">Settings</h1>
      <p className="mb-6 text-sm text-forge-muted">
        DataForge Analytics v{APP_VERSION}
        {health?.version ? ` · API v${health.version}` : ""}
      </p>

      <Card title="Backend status" className="mb-4">
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-forge-muted">Connection</dt>
            <dd className="font-medium capitalize text-forge-text">{state}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-forge-muted">Database</dt>
            <dd>{health?.database ?? "—"}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-forge-muted">Polars / DuckDB</dt>
            <dd>
              {health?.polars ?? "—"} / {health?.duckdb ?? "—"}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-forge-muted">Health URL</dt>
            <dd className="truncate text-xs">{getHealthCheckUrls()[0]}</dd>
          </div>
        </dl>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => retry()}>
            Retry connection
          </Button>
          <Button variant="secondary" onClick={() => openLogsFolder()}>
            Open logs folder
          </Button>
        </div>
      </Card>

      <Card title="Data storage" className="mb-4">
        <dl className="space-y-2 text-sm">
          <div>
            <dt className="text-forge-muted">Data directory</dt>
            <dd className="mt-1 break-all font-mono text-xs text-forge-text">{dataDir}</dd>
          </div>
          <div>
            <dt className="text-forge-muted">Log file</dt>
            <dd className="mt-1 break-all font-mono text-xs text-forge-text">{logFile}</dd>
          </div>
        </dl>
      </Card>

      <Card title="Application data" className="mb-4">
        <p className="mb-3 text-sm text-forge-muted">
          Delete all datasets, uploads, and caches. Logs are kept. This cannot be undone.
        </p>
        <Button
          variant="danger"
          onClick={async () => {
            if (!confirm("Reset all application data? This removes every dataset.")) return;
            await api.resetAppData();
            await queryClient.invalidateQueries();
            alert("Application data reset.");
          }}
        >
          Reset all app data
        </Button>
      </Card>

      <Card title="Demo data" className="mb-4">
        <p className="mb-3 text-sm text-forge-muted">
          Re-import the bundled sales sample dataset (demo UUID).
        </p>
        <Button
          variant="secondary"
          onClick={async () => {
            await api.resetDemo();
            await queryClient.invalidateQueries({ queryKey: ["datasets"] });
            alert("Demo dataset reset.");
          }}
        >
          Reset demo dataset
        </Button>
      </Card>

      <WorkersPanel />

      <Card title="Appearance" className="mb-4">
        <div className="flex flex-wrap gap-2">
          {(["dark", "light", "midnight", "enterprise", "cyberpunk"] as Theme[]).map((t) => (
            <Button
              key={t}
              variant={theme === t ? "primary" : "secondary"}
              onClick={() => setTheme(t)}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </Button>
          ))}
        </div>
      </Card>

      <Card title="API connection">
        <p className="mb-3 text-sm text-forge-muted">
          API base must include <code className="text-forge-text">/api/v1</code>. Origin:{" "}
          {getServerOrigin()}
        </p>
        <input
          className="mb-3 w-full max-w-lg rounded-lg border border-forge-border bg-forge-surface px-4 py-2 text-sm text-forge-text"
          value={apiUrl}
          onChange={(e) => setApiUrl(e.target.value)}
        />
        <Button
          onClick={() => {
            setApiBase(apiUrl);
            retry();
            alert("API URL saved.");
          }}
        >
          Save API URL
        </Button>
      </Card>
    </div>
  );
}
