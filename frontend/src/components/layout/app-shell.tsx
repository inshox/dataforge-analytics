"use client";

import { useState } from "react";
import { Sidebar } from "./sidebar";
import { useAppStore } from "@/store/app-store";
import { cn } from "@/lib/utils";
import { BackendStatus } from "@/components/backend-status";
import { SplashScreen } from "@/components/layout/splash-screen";
import { AboutModal } from "@/components/layout/about-modal";
import { CommandPalette } from "@/components/enterprise/command-palette";
import { WorkspaceTabs } from "@/components/layout/workspace-tabs";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import { APP_VERSION } from "@/lib/desktop";

export function AppShell({ children }: { children: React.ReactNode }) {
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const [aboutOpen, setAboutOpen] = useState(false);
  useKeyboardShortcuts([]);

  return (
    <div className="min-h-screen bg-forge-bg bg-forge-gradient">
      <SplashScreen />
      <CommandPalette />
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
      <Sidebar />
      <main
        className={cn(
          "min-h-screen transition-all duration-300",
          collapsed ? "pl-[72px]" : "pl-64"
        )}
      >
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-forge-border bg-forge-bg/95 px-6 backdrop-blur-md">
          <BackendStatus />
          <button
            type="button"
            className="text-xs text-forge-muted hover:text-forge-text"
            onClick={() => setAboutOpen(true)}
          >
            DataForge Analytics v{APP_VERSION}
          </button>
        </header>
        <div className="p-6">
          <WorkspaceTabs />
          {children}
        </div>
      </main>
    </div>
  );
}
