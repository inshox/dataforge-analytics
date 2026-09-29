import type { FilterCondition, SortSpec } from "@/lib/api";

/** Stable empty refs — avoid `|| []` in selectors (new array every render → infinite React Query updates). */
export const EMPTY_FILTERS: FilterCondition[] = [];
export const EMPTY_SORT: SortSpec[] = [];
