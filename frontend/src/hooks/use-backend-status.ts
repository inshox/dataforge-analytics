"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type HealthInfo } from "@/lib/api";

export type BackendState = "starting" | "online" | "offline";

const STARTUP_GRACE_MS = 22_000;

export function useBackendStatus() {
  const queryClient = useQueryClient();
  const mountedAt = useRef(Date.now());
  const [graceExpired, setGraceExpired] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setGraceExpired(true), STARTUP_GRACE_MS);
    return () => clearTimeout(t);
  }, []);

  const {
    data: health,
    isLoading,
    isFetching,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["health-detail"],
    queryFn: () => api.fetchHealth(),
    retry: (failureCount) => failureCount < 12,
    retryDelay: (attempt) => Math.min(800 * (attempt + 1), 4000),
    refetchInterval: (q) => (q.state.data?.status === "ok" ? 20_000 : 2_500),
    staleTime: 3_000,
  });

  const online = health?.status === "ok";

  let state: BackendState = "starting";
  if (online) {
    state = "online";
  } else if (graceExpired && !isLoading) {
    state = "offline";
  } else if (!graceExpired) {
    state = "starting";
  } else if (isError || (!online && !isFetching)) {
    state = "offline";
  }

  const retry = useCallback(() => {
    api.logApiConfig();
    void queryClient.invalidateQueries({ queryKey: ["health-detail"] });
    void refetch();
  }, [queryClient, refetch]);

  return {
    state,
    health: health as HealthInfo | undefined,
    isChecking: isLoading || isFetching,
    retry,
  };
}
