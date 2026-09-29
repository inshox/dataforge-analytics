import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FilterCondition, SortSpec } from "@/lib/api";

export type Theme = "dark" | "light" | "midnight" | "enterprise" | "cyberpunk";

type AppState = {
  theme: Theme;
  sidebarCollapsed: boolean;
  setTheme: (t: Theme) => void;
  toggleSidebar: () => void;
  tableFilters: Record<string, FilterCondition[]>;
  tableSort: Record<string, SortSpec[]>;
  globalSearch: Record<string, string>;
  hiddenColumns: Record<string, string[]>;
  columnWidths: Record<string, Record<string, number>>;
  setTableFilters: (datasetId: string, filters: FilterCondition[]) => void;
  setTableSort: (datasetId: string, sort: SortSpec[]) => void;
  setGlobalSearch: (datasetId: string, q: string) => void;
  setHiddenColumns: (datasetId: string, cols: string[]) => void;
  setColumnWidth: (datasetId: string, column: string, width: number) => void;
};

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: "dark",
      sidebarCollapsed: false,
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      tableFilters: {},
      tableSort: {},
      globalSearch: {},
      hiddenColumns: {},
      columnWidths: {},
      setTableFilters: (datasetId, filters) =>
        set((s) => ({ tableFilters: { ...s.tableFilters, [datasetId]: filters } })),
      setTableSort: (datasetId, sort) =>
        set((s) => ({ tableSort: { ...s.tableSort, [datasetId]: sort } })),
      setGlobalSearch: (datasetId, q) =>
        set((s) => ({ globalSearch: { ...s.globalSearch, [datasetId]: q } })),
      setHiddenColumns: (datasetId, cols) =>
        set((s) => ({ hiddenColumns: { ...s.hiddenColumns, [datasetId]: cols } })),
      setColumnWidth: (datasetId, column, width) =>
        set((s) => ({
          columnWidths: {
            ...s.columnWidths,
            [datasetId]: { ...(s.columnWidths[datasetId] ?? {}), [column]: width },
          },
        })),
    }),
    {
      name: "dataforge-app",
      skipHydration: true,
      partialize: (s) => ({
        theme: s.theme,
        sidebarCollapsed: s.sidebarCollapsed,
        tableFilters: s.tableFilters,
        tableSort: s.tableSort,
        globalSearch: s.globalSearch,
        hiddenColumns: s.hiddenColumns,
        columnWidths: s.columnWidths,
      }),
    }
  )
);
