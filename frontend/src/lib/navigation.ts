/**
 * Dataset navigation — uses /datasets/view/?id= so Tauri static export works
 * (no per-UUID HTML files required).
 */

export type DatasetTab = "overview" | "table" | "analysis" | "charts" | "sql" | "analyst";

export function datasetHref(id: string, tab: DatasetTab = "overview"): string {
  const params = new URLSearchParams({ id });
  if (tab !== "overview") params.set("tab", tab);
  return `/datasets/view/?${params.toString()}`;
}

export function parseDatasetView(
  searchParams: URLSearchParams | { get: (k: string) => string | null }
): { id: string; tab: DatasetTab } | null {
  const id = searchParams.get("id")?.trim();
  if (!id) return null;
  const tab = (searchParams.get("tab") as DatasetTab) || "overview";
  const allowed: DatasetTab[] = ["overview", "table", "analysis", "charts", "sql", "analyst"];
  return { id, tab: allowed.includes(tab) ? tab : "overview" };
}
