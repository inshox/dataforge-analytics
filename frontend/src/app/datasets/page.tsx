"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import { ImportWizard } from "@/components/data/import-wizard";
import { DatasetCard } from "@/components/dataset/dataset-card";
import { EmptyState } from "@/components/ui/empty-state";

export default function DatasetsPage() {
  const [search, setSearch] = useState("");
  const { data: datasets = [], isLoading } = useQuery({
    queryKey: ["datasets", search],
    queryFn: () => api.listDatasets(search || undefined),
  });

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-forge-text">Datasets</h1>
      <p className="mb-6 text-forge-muted">Import, search, and manage your data projects.</p>

      <ImportWizard />

      <div className="mt-8">
        <div className="relative mb-4 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-forge-muted" />
          <input
            className="w-full rounded-lg border border-forge-border bg-forge-surface py-2 pl-10 pr-4 text-sm"
            placeholder="Search datasets…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {isLoading ? (
          <p className="text-forge-muted">Loading…</p>
        ) : datasets.length === 0 ? (
          <EmptyState title="No datasets" description="Upload a CSV file above to create your first dataset." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {datasets.map((d) => (
              <DatasetCard key={d.id} dataset={d} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
