import type { ReactNode } from "react";

export default function DatasetIdLayout({ children }: { children: ReactNode }) {
  return children;
}

/** Tauri static export: one placeholder HTML shell; real IDs are resolved client-side. */
export function generateStaticParams() {
  if (process.env.TAURI_BUILD === "1") {
    return [{ id: "placeholder" }];
  }
  return [];
}

export const dynamicParams = true;
