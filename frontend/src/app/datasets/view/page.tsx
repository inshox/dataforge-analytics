"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DatasetIdProvider } from "@/contexts/dataset-id-context";
import { parseDatasetView } from "@/lib/navigation";
import DatasetOverviewPage from "../[id]/page";
import DatasetTablePage from "../[id]/table/page";
import DatasetAnalysisPage from "../[id]/analysis/page";
import DatasetChartsPage from "../[id]/charts/page";
import DatasetSqlPage from "../[id]/sql/page";
import AnalystPage from "../[id]/analyst/page";

function DatasetViewInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const parsed = parseDatasetView(searchParams);

  useEffect(() => {
    if (parsed) {
      console.info("[DataForge] Dataset view:", parsed.id, "tab:", parsed.tab);
    }
  }, [parsed]);

  if (!parsed) {
    return (
      <div className="rounded-lg border border-forge-border bg-forge-surface p-8 text-center">
        <p className="text-forge-muted">Brak identyfikatora datasetu.</p>
        <button
          type="button"
          className="mt-4 text-sm text-indigo-300 hover:underline"
          onClick={() => router.push("/datasets/")}
        >
          Wróć do listy
        </button>
      </div>
    );
  }

  const { id, tab } = parsed;

  let content: React.ReactNode;
  switch (tab) {
    case "table":
      content = <DatasetTablePage />;
      break;
    case "analysis":
      content = <DatasetAnalysisPage />;
      break;
    case "charts":
      content = <DatasetChartsPage />;
      break;
    case "sql":
      content = <DatasetSqlPage />;
      break;
    case "analyst":
      content = <AnalystPage />;
      break;
    default:
      content = <DatasetOverviewPage />;
  }

  return <DatasetIdProvider datasetId={id}>{content}</DatasetIdProvider>;
}

export default function DatasetViewPage() {
  return (
    <Suspense fallback={<p className="text-forge-muted">Loading dataset…</p>}>
      <DatasetViewInner />
    </Suspense>
  );
}
