"use client";

import { useParams } from "next/navigation";
import { useDatasetIdFromContext } from "@/contexts/dataset-id-context";

/** Resolves dataset id from dynamic segment or /datasets/view?id= (Tauri static export). */
export function useDatasetRoute() {
  const fromContext = useDatasetIdFromContext();
  const params = useParams<{ id: string }>();
  const rawId = fromContext ?? params?.id ?? "";
  const isPlaceholder = rawId === "placeholder";
  return {
    id: isPlaceholder ? "" : rawId,
    isPlaceholder,
    ready: !isPlaceholder && rawId.length > 0,
  };
}
