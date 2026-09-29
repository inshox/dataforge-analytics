"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useAppStore } from "@/store/app-store";
import { DesktopApiBootstrap } from "@/components/desktop-api-bootstrap";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );
  const [ready, setReady] = useState(false);
  const theme = useAppStore((s) => s.theme);

  useEffect(() => {
    const done = () => setReady(true);
    const result = useAppStore.persist.rehydrate();
    if (result instanceof Promise) {
      void result.then(done);
    } else {
      done();
    }
  }, []);

  useEffect(() => {
    if (!ready) return;
    const themes = ["dark", "light", "midnight", "enterprise", "cyberpunk"] as const;
    for (const t of themes) {
      document.documentElement.classList.toggle(t, theme === t);
    }
  }, [theme, ready]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-forge-bg text-forge-muted">
        Loading…
      </div>
    );
  }

  return (
    <QueryClientProvider client={client}>
      <DesktopApiBootstrap />
      {children}
    </QueryClientProvider>
  );
}
