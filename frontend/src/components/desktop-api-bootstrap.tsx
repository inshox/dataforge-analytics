"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getDesktopPaths, isTauri } from "@/lib/desktop";
import { setApiBase } from "@/lib/api";

/** Sync API URL from backend.port when running inside Tauri. */
export function DesktopApiBootstrap() {
  const queryClient = useQueryClient();

  useEffect(() => {
    let cancelled = false;

    async function sync() {
      if (!(await isTauri())) return;
      const paths = await getDesktopPaths();
      if (cancelled || !paths) return;
      const port = paths.backend_port;
      if (port) {
        setApiBase(`http://127.0.0.1:${port}/api/v1`);
        void queryClient.invalidateQueries({ queryKey: ["health-detail"] });
      }
    }

    void sync();
    const interval = setInterval(() => void sync(), 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [queryClient]);

  return null;
}
