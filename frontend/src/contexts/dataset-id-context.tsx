"use client";

import { createContext, useContext } from "react";

const DatasetIdContext = createContext<string | null>(null);

export function DatasetIdProvider({
  datasetId,
  children,
}: {
  datasetId: string;
  children: React.ReactNode;
}) {
  return <DatasetIdContext.Provider value={datasetId}>{children}</DatasetIdContext.Provider>;
}

export function useDatasetIdFromContext(): string | null {
  return useContext(DatasetIdContext);
}
