"use client";

import { BarChart3 } from "lucide-react";
import { useBackendStatus } from "@/hooks/use-backend-status";

export function SplashScreen() {
  const { state } = useBackendStatus();

  if (state === "online") return null;

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-forge-bg">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-forge-border bg-forge-card">
        <BarChart3 className="h-9 w-9 text-forge-text" />
      </div>
      <h1 className="text-xl font-semibold text-forge-text">DataForge Analytics</h1>
      <p className="mt-2 text-sm text-forge-muted">
        {state === "starting" ? "Starting analytics engine…" : "Connecting to backend…"}
      </p>
      <div className="mt-6 h-1 w-48 overflow-hidden rounded-full bg-forge-hover">
        <div className="h-full w-1/2 animate-pulse rounded-full bg-forge-text" />
      </div>
      <p className="mt-4 text-xs text-forge-muted">v1.0 · Local-first analytics</p>
    </div>
  );
}
