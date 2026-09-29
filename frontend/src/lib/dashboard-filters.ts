import type { DashboardVariable, FilterCondition } from "@/lib/api";

export function variableValuesToQuery(values: Record<string, unknown>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(values)) {
    if (v === null || v === undefined || v === "") continue;
    if (typeof v === "object" && v !== null && "from" in v) {
      const dr = v as { from?: string; to?: string };
      if (dr.from) out[`${k}_from`] = String(dr.from);
      if (dr.to) out[`${k}_to`] = String(dr.to);
    } else if (Array.isArray(v)) {
      out[k] = v.join(",");
    } else {
      out[k] = String(v);
    }
  }
  return out;
}

export function queryToVariableValues(
  variables: DashboardVariable[],
  searchParams: URLSearchParams
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const v of variables) {
    if (v.type === "date_range") {
      const from = searchParams.get(`${v.name}_from`);
      const to = searchParams.get(`${v.name}_to`);
      if (from || to) {
        out[v.name] = { from: from ?? "", to: to ?? "" };
        continue;
      }
    }
    const raw = searchParams.get(v.name);
    if (raw !== null) {
      if (v.type === "multi_select") out[v.name] = raw.split(",").filter(Boolean);
      else if (v.type === "boolean") out[v.name] = raw === "true";
      else if (v.type === "number") out[v.name] = Number(raw);
      else out[v.name] = raw;
    } else if (v.current_value !== undefined && v.current_value !== null) {
      out[v.name] = v.current_value;
    } else {
      out[v.name] = v.default_value;
    }
  }
  return out;
}

export function variablesToFilterConditions(
  variables: DashboardVariable[],
  values: Record<string, unknown>
): FilterCondition[] {
  const filters: FilterCondition[] = [];
  for (const v of variables) {
    const col = v.column_name || v.name;
    const val = values[v.name];
    if (val === null || val === undefined || val === "" || (Array.isArray(val) && !val.length)) {
      continue;
    }
    if (v.type === "date_range" && typeof val === "object" && val !== null) {
      const dr = val as { from?: string; to?: string };
      if (dr.from && dr.to) {
        filters.push({
          column: col,
          operator: "between",
          value: dr.from,
          value_to: dr.to,
        });
      }
      continue;
    }
    if (v.type === "multi_select" && Array.isArray(val)) {
      filters.push({ column: col, operator: "in_list", value: val });
      continue;
    }
    filters.push({ column: col, operator: "equals", value: val });
  }
  return filters;
}

export function buildDrillthroughHref(
  targetDashboardId: string,
  variableName: string,
  value: string
): string {
  const params = new URLSearchParams();
  params.set("id", targetDashboardId);
  params.set(variableName, value);
  return `/dashboards/view?${params.toString()}`;
}
