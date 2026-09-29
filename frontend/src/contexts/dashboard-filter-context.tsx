"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type DashboardVariable, type FilterCondition, type WidgetVariableFilter } from "@/lib/api";
import {
  queryToVariableValues,
  variableValuesToQuery,
  variablesToFilterConditions,
} from "@/lib/dashboard-filters";

type Ctx = {
  variables: DashboardVariable[];
  values: Record<string, unknown>;
  setVariable: (name: string, value: unknown) => void;
  resetFilters: () => void;
  saveDefaults: () => void;
  globalFilters: FilterCondition[];
  filterVersion: number;
  getWidgetExtraFilters: (settings: Record<string, unknown>) => FilterCondition[];
  applyCrossFilter: (variableName: string, value: unknown, column?: string) => void;
  clearVariable: (name: string) => void;
  filterPresets: Array<{ id: string; name: string; values: Record<string, unknown> }>;
  saveFilterPreset: (name: string) => Promise<void>;
  loadFilterPreset: (presetId: string) => void;
};

const DashboardFilterContext = createContext<Ctx | null>(null);

export function DashboardFilterProvider({
  dashboardId,
  children,
}: {
  dashboardId: string;
  children: ReactNode;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const qc = useQueryClient();
  const [filterVersion, setFilterVersion] = useState(0);

  const { data: variables = [] } = useQuery({
    queryKey: ["dashboard-variables", dashboardId],
    queryFn: () => api.listDashboardVariables(dashboardId),
  });

  const { data: filterPresets = [], refetch: refetchPresets } = useQuery({
    queryKey: ["filter-presets", dashboardId],
    queryFn: () => api.listFilterPresets(dashboardId),
  });

  const values = useMemo(
    () => queryToVariableValues(variables, searchParams),
    [variables, searchParams]
  );

  const syncUrl = useCallback(
    (next: Record<string, unknown>) => {
      const params = new URLSearchParams();
      params.set("id", dashboardId);
      const q = variableValuesToQuery(next);
      for (const [k, v] of Object.entries(q)) {
        params.set(k, v);
      }
      router.replace(`/dashboards/view?${params.toString()}`);
      if (typeof window !== "undefined") {
        localStorage.setItem(`df-dash-vars-${dashboardId}`, JSON.stringify(next));
      }
    },
    [dashboardId, router]
  );

  useEffect(() => {
    if (!variables.length || searchParams.get("id") !== dashboardId) return;
    const hasVarParams = variables.some((v) => searchParams.has(v.name) || searchParams.has(`${v.name}_from`));
    if (hasVarParams) return;
    const stored = localStorage.getItem(`df-dash-vars-${dashboardId}`);
    if (stored) {
      try {
        syncUrl(JSON.parse(stored) as Record<string, unknown>);
      } catch {
        /* ignore */
      }
    }
  }, [variables, dashboardId, searchParams, syncUrl]);

  const persist = useMutation({
    mutationFn: (vals: Record<string, unknown>) =>
      api.bulkUpdateDashboardVariables(dashboardId, vals),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["dashboard-variables", dashboardId] });
      setFilterVersion((v) => v + 1);
    },
  });

  const setVariable = useCallback(
    (name: string, value: unknown) => {
      const next = { ...values, [name]: value };
      syncUrl(next);
      void persist.mutateAsync(next);
    },
    [values, syncUrl, persist]
  );

  const resetFilters = useCallback(() => {
    const next: Record<string, unknown> = {};
    for (const v of variables) {
      next[v.name] = v.default_value ?? "";
    }
    syncUrl(next);
    void persist.mutateAsync(next);
  }, [variables, syncUrl, persist]);

  const saveDefaults = useCallback(async () => {
    for (const v of variables) {
      await api.updateDashboardVariable(dashboardId, v.id, {
        default_value: values[v.name],
        current_value: values[v.name],
      });
    }
    void qc.invalidateQueries({ queryKey: ["dashboard-variables", dashboardId] });
  }, [variables, values, dashboardId, qc]);

  const globalFilters = useMemo(
    () => variablesToFilterConditions(variables, values),
    [variables, values, filterVersion]
  );

  const getWidgetExtraFilters = useCallback(
    (settings: Record<string, unknown>) => {
      const bindings = (settings.variable_filters || settings.filters || []) as WidgetVariableFilter[];
      const byId = Object.fromEntries(variables.map((v) => [v.id, v]));
      const byName = Object.fromEntries(variables.map((v) => [v.name, v]));
      const extra: FilterCondition[] = [];
      for (const b of bindings) {
        const v = byId[b.variable_id] || byName[b.variable_id];
        if (!v) continue;
        const val = values[v.name];
        if (val === null || val === undefined || val === "") continue;
        const col = b.column || v.column_name || v.name;
        const op =
          b.operator === "eq"
            ? "equals"
            : b.operator === "neq"
              ? "not_equals"
              : b.operator === "in"
                ? "in_list"
                : b.operator === "gte"
                  ? "greater_or_equal"
                  : b.operator === "lte"
                    ? "less_or_equal"
                    : b.operator === "gt"
                      ? "greater_than"
                      : b.operator === "lt"
                        ? "less_than"
                        : b.operator;
        extra.push({ column: col, operator: op as FilterCondition["operator"], value: val });
      }
      return extra;
    },
    [variables, values]
  );

  const applyCrossFilter = useCallback(
    (variableName: string, value: unknown) => {
      setVariable(variableName, value);
    },
    [setVariable]
  );

  const clearVariable = useCallback(
    (name: string) => {
      const v = variables.find((x) => x.name === name);
      setVariable(name, v?.default_value ?? "");
    },
    [variables, setVariable]
  );

  const saveFilterPreset = useCallback(
    async (name: string) => {
      await api.createFilterPreset(dashboardId, name, values);
      await refetchPresets();
    },
    [dashboardId, values, refetchPresets]
  );

  const loadFilterPreset = useCallback(
    (presetId: string) => {
      const preset = filterPresets.find((p) => p.id === presetId);
      if (preset) {
        syncUrl(preset.values);
        void persist.mutateAsync(preset.values);
      }
    },
    [filterPresets, syncUrl, persist]
  );

  const ctx: Ctx = {
    variables,
    values,
    setVariable,
    resetFilters,
    saveDefaults,
    globalFilters,
    filterVersion,
    getWidgetExtraFilters,
    applyCrossFilter,
    clearVariable,
    filterPresets,
    saveFilterPreset,
    loadFilterPreset,
  };

  return (
    <DashboardFilterContext.Provider value={ctx}>{children}</DashboardFilterContext.Provider>
  );
}

export function useDashboardFilters() {
  const ctx = useContext(DashboardFilterContext);
  if (!ctx) throw new Error("useDashboardFilters requires DashboardFilterProvider");
  return ctx;
}
