import type { ReactNode } from "react";

export default function DashboardIdLayout({ children }: { children: ReactNode }) {
  return children;
}

export function generateStaticParams() {
  if (process.env.TAURI_BUILD === "1") {
    return [{ id: "placeholder" }];
  }
  return [];
}

export const dynamicParams = true;
