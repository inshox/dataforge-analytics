"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

type Shortcut = {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  action: () => void;
};

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
          /* allow command palette */
        } else {
          return;
        }
      }
      for (const s of shortcuts) {
        const mod = s.ctrl ? e.ctrlKey || e.metaKey : !e.ctrlKey && !e.metaKey;
        const shift = s.shift ? e.shiftKey : !e.shiftKey;
        if (mod && shift && e.key.toLowerCase() === s.key.toLowerCase()) {
          e.preventDefault();
          s.action();
          return;
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "d") {
        e.preventDefault();
        router.push("/datasets");
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        router.push("/dashboards");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [shortcuts, router]);
}
