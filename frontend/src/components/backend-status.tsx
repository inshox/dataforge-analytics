"use client";

import { RefreshCw } from "lucide-react";
import { useBackendStatus } from "@/hooks/use-backend-status";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const LABELS = {
  starting: "Starting backend…",
  online: "Backend online",
  offline: "Backend offline",
} as const;

export function BackendStatus() {
  const { state, health, isChecking, retry } = useBackendStatus();

  return (
    <div className="flex items-center gap-3 text-sm">
      <span
        className={cn(
          "h-2.5 w-2.5 shrink-0 rounded-full",
          state === "starting" && "animate-pulse bg-neutral-400",
          state === "online" && "bg-forge-success-fg",
          state === "offline" && "bg-red-500"
        )}
      />
      <div className="min-w-0">
        <span className="text-forge-muted">{LABELS[state]}</span>
        {state === "online" && health?.version && (
          <span className="ml-2 text-xs text-forge-muted/80">v{health.version}</span>
        )}
      </div>
      <Button
        variant="ghost"
        className="h-8 px-2"
        onClick={() => retry()}
        disabled={isChecking && state === "starting"}
        title="Retry connection"
      >
        <RefreshCw className={cn("h-4 w-4", isChecking && "animate-spin")} />
      </Button>
    </div>
  );
}
