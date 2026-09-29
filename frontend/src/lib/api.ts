/**
 * API client — talks to local FastAPI backend.
 */

const DEFAULT_ORIGIN = "http://127.0.0.1:8000";
const DEFAULT_API = `${DEFAULT_ORIGIN}/api/v1`;

function migrateStoredApiUrl(): void {
  if (typeof window === "undefined") return;
  const stored = localStorage.getItem("dataforge_api_url");
  if (!stored) return;
  try {
    const url = new URL(stored.trim());
    const path = url.pathname.replace(/\/$/, "") || "/";
    if (path === "/") {
      const normalized = `${url.origin}/api/v1`;
      localStorage.setItem("dataforge_api_url", normalized);
      console.info("[DataForge] Migrated API URL to:", normalized);
    }
  } catch {
    localStorage.removeItem("dataforge_api_url");
  }
}

function readConfiguredUrl(): string {
  if (typeof window !== "undefined") {
    migrateStoredApiUrl();
    return (
      localStorage.getItem("dataforge_api_url") ||
      process.env.NEXT_PUBLIC_API_URL ||
      DEFAULT_API
    );
  }
  return process.env.NEXT_PUBLIC_API_URL || DEFAULT_API;
}

/** Server origin without API path, e.g. http://127.0.0.1:8000 */
export function getServerOrigin(): string {
  const raw = readConfiguredUrl().trim();
  try {
    const url = new URL(raw);
    return url.origin;
  } catch {
    return DEFAULT_ORIGIN;
  }
}

/** REST base including /api/v1 — normalizes bare http://127.0.0.1:8000 */
export function getApiBase(): string {
  const raw = readConfiguredUrl().trim();
  try {
    const url = new URL(raw);
    const path = url.pathname.replace(/\/$/, "");
    if (!path || path === "/") {
      return `${url.origin}/api/v1`;
    }
    if (path === "/api/v1" || path.startsWith("/api/v1/")) {
      return `${url.origin}/api/v1`;
    }
    return `${url.origin}/api/v1`;
  } catch {
    return DEFAULT_API;
  }
}

/** Health endpoints (FastAPI registers both). */
export function getHealthCheckUrls(): string[] {
  const origin = getServerOrigin();
  return [`${origin}/health`, `${origin}/api/v1/health`];
}

export function setApiBase(url: string) {
  localStorage.setItem("dataforge_api_url", url.trim());
}

export type HealthCheckResult = {
  ok: boolean;
  url: string;
  status: number;
  body: string;
};

export type HealthInfo = {
  status: string;
  service: string;
  version: string;
  database: string;
  data_directory: string;
  log_file: string;
  duckdb: string;
  polars: string;
  polars_version?: string;
  duckdb_version?: string;
  host?: string;
  port?: number;
};

function parseErrorMessage(text: string, status: number): string {
  try {
    const j = JSON.parse(text) as { message?: string; detail?: string };
    return j.message || j.detail || text || `HTTP ${status}`;
  } catch {
    return text || `HTTP ${status}`;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
      Authorization: "Bearer demo-token",
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(parseErrorMessage(text, res.status));
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res as unknown as T;
}

export type ColumnInfo = { name: string; dtype: string; nullable: boolean };

export type DatasetSummary = {
  id: string;
  name: string;
  description?: string;
  tags: string[];
  source_filename?: string;
  source_format?: string;
  file_size_bytes?: number;
  row_count: number;
  column_count: number;
  columns: ColumnInfo[];
  status: string;
  import_progress: number;
  import_stage?: string | null;
  created_at?: string;
};

export type FilterOperator =
  | "equals"
  | "not_equals"
  | "contains"
  | "starts_with"
  | "greater_than"
  | "less_than"
  | "greater_or_equal"
  | "less_or_equal"
  | "between"
  | "in_list"
  | "is_empty"
  | "is_not_empty";

export type FilterCondition = {
  column: string;
  operator: FilterOperator;
  value?: unknown;
  value_to?: unknown;
};

export type SortSpec = { column: string; descending: boolean };

export type ChartNode = {
  id: string;
  name: string;
  value?: number | null;
  parent?: string | null;
  color?: string | null;
};

export type ChartLink = { source: string; target: string; value: number };

export type ChartDataPoint = {
  label: string;
  value: number;
  series?: string | null;
  extra?: Record<string, unknown>;
};

export type ChartResponse = {
  chart_type: string;
  data: ChartDataPoint[];
  nodes?: ChartNode[];
  links?: ChartLink[];
  series?: Record<string, unknown>[];
  meta?: Record<string, unknown>;
};

export type TopValue = { value: string; count: number };

export type ColumnProfile = {
  column: string;
  dtype: string;
  inferred_type: string;
  count: number;
  null_count: number;
  null_percent: number;
  unique_count: number;
  mean?: number;
  median?: number;
  min?: number;
  max?: number;
  std?: number;
  outlier_count: number;
  top_values: TopValue[];
};

export type DatasetProfile = {
  dataset_id: string;
  row_count: number;
  column_count: number;
  duplicate_rows: number;
  columns: ColumnProfile[];
  correlations: { column_a: string; column_b: string; correlation: number }[];
  insights: string[];
};

export type AiAnalystResult = {
  sql: string;
  explanation: string;
  suggested_chart_type?: string | null;
  suggested_x_column?: string | null;
  suggested_y_column?: string | null;
};

export type SqlResult = {
  columns: string[];
  rows: Record<string, unknown>[];
  page: number;
  page_size: number;
  total_rows: number;
};

export type TableViewSpec = {
  name: string;
  filters: FilterCondition[];
  sort: SortSpec[];
  hidden_columns: string[];
};

export type TableView = TableViewSpec & { id: string; created_at?: string | null };

export type DashboardWidget = {
  id?: string;
  widget_type: string;
  dataset_id?: string | null;
  chart_type?: string | null;
  sql_query?: string | null;
  x: number;
  y: number;
  w: number;
  h: number;
  settings: Record<string, unknown>;
};

export type DashboardSummary = {
  id: string;
  name: string;
  description?: string | null;
  widget_count: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type DashboardDetail = DashboardSummary & {
  widgets: DashboardWidget[];
  layout_json?: string | null;
};

export type DashboardVariable = {
  id: string;
  dashboard_id: string;
  name: string;
  label: string;
  type: string;
  column_name?: string | null;
  dataset_id?: string | null;
  default_value?: unknown;
  current_value?: unknown;
  allowed_values?: unknown[];
};

export type WidgetVariableFilter = {
  variable_id: string;
  column: string;
  operator: string;
};

export type DashboardDrillthroughRule = {
  id: string;
  source_dashboard_id: string;
  source_widget_id?: string | null;
  target_dashboard_id: string;
  trigger_column: string;
  target_variable_name: string;
  label: string;
  open_mode: string;
};

export type InsightItem = {
  id: string;
  category: string;
  severity: string;
  message: string;
  metric?: string | null;
  value?: number | null;
};

export type ChartTemplate = {
  id: string;
  name: string;
  dataset_id: string;
  chart_type: string;
  config: Record<string, unknown>;
  created_at?: string | null;
};

export type Relationship = {
  id: string;
  left_dataset_id: string;
  right_dataset_id: string;
  left_column: string;
  right_column: string;
  relationship_type: string;
  confidence: number;
  is_manual: boolean;
  created_at?: string | null;
};

export type SavedQuery = {
  id: string;
  name: string;
  dataset_id?: string | null;
  sql_text: string;
  created_at?: string | null;
  updated_at?: string | null;
};

export type QueryHistoryEntry = {
  id: string;
  dataset_id?: string | null;
  sql_text: string;
  runtime_ms: number;
  rows_returned: number;
  success: boolean;
  error_message?: string | null;
  created_at?: string | null;
};

export type ForecastPoint = {
  date: string;
  value: number;
  lower?: number | null;
  upper?: number | null;
  is_forecast: boolean;
};

function logApiConfig(): void {
  if (typeof window === "undefined") return;
  console.info("[DataForge] API base:", getApiBase());
  console.info("[DataForge] Server origin:", getServerOrigin());
  console.info("[DataForge] Health URLs:", getHealthCheckUrls().join(", "));
}

async function fetchHealth(): Promise<HealthInfo | null> {
  logApiConfig();
  const urls = getHealthCheckUrls();

  for (const healthUrl of urls) {
    try {
      console.info("[DataForge] Health check →", healthUrl);
      const res = await fetch(healthUrl, {
        method: "GET",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      const body = await res.text();
      console.info("[DataForge] Health response:", res.status, body);

      if (res.ok) {
        return JSON.parse(body) as HealthInfo;
      }
    } catch (err) {
      console.warn("[DataForge] Health fetch failed:", healthUrl, err);
    }
  }
  return null;
}

export const api = {
  logApiConfig,
  fetchHealth,
  checkHealth: async () => (await fetchHealth())?.status === "ok",

  async checkHealthDetailed(): Promise<HealthCheckResult> {
    logApiConfig();
    const urls = getHealthCheckUrls();
    let last: HealthCheckResult = { ok: false, url: urls[0], status: 0, body: "" };

    for (const healthUrl of urls) {
      try {
        const res = await fetch(healthUrl, { method: "GET", cache: "no-store" });
        const body = await res.text();
        last = { ok: res.ok, url: healthUrl, status: res.status, body };
        if (res.ok) return last;
      } catch (err) {
        last = {
          ok: false,
          url: healthUrl,
          status: 0,
          body: err instanceof Error ? err.message : String(err),
        };
      }
    }
    return last;
  },

  listDatasets: (search?: string) =>
    request<DatasetSummary[]>(`/datasets${search ? `?search=${encodeURIComponent(search)}` : ""}`),

  getDataset: (id: string) => request<DatasetSummary>(`/datasets/${id}`),

  importPreview: async (file: File, name?: string, separator?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (name) fd.append("name", name);
    if (separator) fd.append("separator", separator);
    const res = await fetch(`${getApiBase()}/datasets/import/preview`, {
      method: "POST",
      body: fd,
      headers: { Authorization: "Bearer demo-token" },
    });
    if (!res.ok) throw new Error(parseErrorMessage(await res.text(), res.status));
    return res.json() as Promise<{
      dataset_id: string;
      preview_rows: Record<string, unknown>[];
      columns: ColumnInfo[];
      row_count_estimate?: number;
      file_size_bytes: number;
      detected_separator?: string;
      detected_encoding?: string;
      detected_format?: string;
      validation_warnings?: string[];
    }>;
  },

  cancelImport: (id: string) =>
    request<{ ok: boolean }>(`/datasets/${id}/import/cancel`, { method: "POST" }),

  resetDemo: () =>
    request<{ ok: boolean; dataset_id?: string; name?: string; message?: string }>(
      "/system/reset-demo",
      { method: "POST" }
    ),

  resetAppData: () =>
    request<{ ok: boolean; message?: string }>("/system/reset-app-data", { method: "POST" }),

  finalizeImport: (id: string, background = false) =>
    request<DatasetSummary>(
      `/datasets/${id}/import/finalize${background ? "?background=true" : ""}`,
      { method: "POST" }
    ),

  aggregate: (
    id: string,
    body: { group_by: string[]; aggregations: Record<string, string> }
  ) =>
    request<{ dataset_id: string; columns: string[]; rows: Record<string, unknown>[] }>(
      `/datasets/${id}/aggregate`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    ),

  getRows: (
    id: string,
    params: {
      page?: number;
      page_size?: number;
      sort?: SortSpec[];
      filters?: FilterCondition[];
      q?: string;
    }
  ) => {
    const sp = new URLSearchParams();
    sp.set("page", String(params.page ?? 1));
    sp.set("page_size", String(params.page_size ?? 100));
    if (params.sort?.length) sp.set("sort", JSON.stringify(params.sort));
    if (params.filters?.length) sp.set("filters", JSON.stringify(params.filters));
    if (params.q) sp.set("q", params.q);
    return request<{
      rows: Record<string, unknown>[];
      page: number;
      page_size: number;
      total_rows: number;
      total_pages: number;
      columns: ColumnInfo[];
    }>(`/datasets/${id}/rows?${sp}`);
  },

  getStats: (id: string) =>
    request<{
      dataset_id: string;
      row_count: number;
      column_count: number;
      duplicate_rows: number;
      columns: Array<{
        column: string;
        dtype: string;
        count: number;
        null_count: number;
        unique_count: number;
        mean?: number;
        median?: number;
        min?: number;
        max?: number;
        std?: number;
      }>;
    }>(`/datasets/${id}/stats`),

  getProfile: (id: string) =>
    request<DatasetProfile>(`/datasets/${id}/profile`),

  aiAnalyze: (id: string, question: string) =>
    request<AiAnalystResult>(`/datasets/${id}/ai/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),

  aiExecute: (id: string, sql: string, page = 1, page_size = 100) =>
    request<SqlResult>(`/datasets/${id}/ai/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql, page, page_size }),
    }),

  reportUrl: (id: string, format: "html" | "pdf" = "html") =>
    `${getApiBase()}/datasets/${id}/report?format=${format}`,

  listViews: (id: string) => request<TableView[]>(`/datasets/${id}/views`),

  saveView: (id: string, spec: TableViewSpec) =>
    request<TableView>(`/datasets/${id}/views`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(spec),
    }),

  deleteView: (id: string, viewId: string) =>
    request<{ ok: boolean }>(`/datasets/${id}/views/${viewId}`, { method: "DELETE" }),

  buildChart: (
    id: string,
    body: {
      chart_type: string;
      x_column: string;
      y_column?: string;
      z_column?: string;
      source_column?: string;
      target_column?: string;
      parent_column?: string;
      aggregation?: string;
      filters?: FilterCondition[];
      limit?: number;
      config?: Record<string, unknown>;
      extra_filters?: FilterCondition[];
    }
  ) =>
    request<ChartResponse>(`/datasets/${id}/charts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  listChartTypes: () => request<{ id: string; category: string }[]>("/charts/types"),

  listDashboardTemplates: () =>
    request<
      { id: string; name: string; category: string; description: string; widget_count: number }[]
    >("/dashboards/templates"),

  instantiateDashboardTemplate: (templateId: string, datasetId: string, name?: string) =>
    request<DashboardDetail>(`/dashboards/templates/${templateId}/instantiate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, name }),
    }),

  workerStats: () =>
    request<{ active_jobs: number; queued_jobs: number; memory_mb?: number; cpu_percent?: number }>(
      "/workers/stats"
    ),

  listWorkers: () =>
    request<
      {
        id: string;
        job_type: string;
        status: string;
        progress: number;
        error_message?: string | null;
      }[]
    >("/workers"),

  submitWorkerJob: (job_type: string, payload: Record<string, unknown>) =>
    request<{ id: string; status: string; progress: number }>("/workers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_type, payload }),
    }),

  runSql: (id: string, query: string, page = 1, page_size = 100) =>
    request<SqlResult>(`/datasets/${id}/sql`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, page, page_size }),
    }),

  exportCsvUrl: (
    id: string,
    params?: { sort?: SortSpec[]; filters?: FilterCondition[]; q?: string }
  ) => {
    const sp = new URLSearchParams();
    if (params?.sort?.length) sp.set("sort", JSON.stringify(params.sort));
    if (params?.filters?.length) sp.set("filters", JSON.stringify(params.filters));
    if (params?.q) sp.set("q", params.q);
    const qs = sp.toString();
    return `${getApiBase()}/datasets/${id}/export/csv${qs ? `?${qs}` : ""}`;
  },

  // Enterprise v1.1
  listDashboards: () => request<DashboardSummary[]>("/dashboards"),
  createDashboard: (name: string, description?: string) =>
    request<DashboardDetail>("/dashboards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    }),
  getDashboard: (id: string) => request<DashboardDetail>(`/dashboards/${id}`),
  saveDashboard: (id: string, body: Partial<DashboardDetail> & { widgets?: DashboardWidget[] }) =>
    request<DashboardDetail>(`/dashboards/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteDashboard: (id: string) =>
    request<{ ok: boolean }>(`/dashboards/${id}`, { method: "DELETE" }),
  duplicateDashboard: (id: string) =>
    request<DashboardDetail>(`/dashboards/${id}/duplicate`, { method: "POST" }),
  dashboardExportUrl: (id: string, format: "pdf" | "html" | "png") =>
    `${getApiBase()}/dashboards/${id}/export?format=${format}`,

  listDashboardVariables: (dashboardId: string) =>
    request<DashboardVariable[]>(`/dashboards/${dashboardId}/variables`),
  createDashboardVariable: (
    dashboardId: string,
    body: Omit<DashboardVariable, "id" | "dashboard_id">
  ) =>
    request<DashboardVariable>(`/dashboards/${dashboardId}/variables`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: body.name,
        label: body.label,
        type: body.type,
        column_name: body.column_name,
        default_value: body.default_value,
        current_value: body.current_value,
        allowed_values: body.allowed_values ?? [],
      }),
    }),
  updateDashboardVariable: (
    dashboardId: string,
    variableId: string,
    body: Partial<DashboardVariable>
  ) =>
    request<DashboardVariable>(`/dashboards/${dashboardId}/variables/${variableId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteDashboardVariable: (dashboardId: string, variableId: string) =>
    request<{ ok: boolean }>(`/dashboards/${dashboardId}/variables/${variableId}`, {
      method: "DELETE",
    }),
  bulkUpdateDashboardVariables: (dashboardId: string, values: Record<string, unknown>) =>
    request<DashboardVariable[]>(`/dashboards/${dashboardId}/variables/bulk`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values }),
    }),

  listDrillthroughRules: (dashboardId: string) =>
    request<DashboardDrillthroughRule[]>(`/dashboards/${dashboardId}/drillthrough`),
  createDrillthroughRule: (
    dashboardId: string,
    body: Omit<DashboardDrillthroughRule, "id" | "source_dashboard_id">
  ) =>
    request<DashboardDrillthroughRule>(`/dashboards/${dashboardId}/drillthrough`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteDrillthroughRule: (dashboardId: string, ruleId: string) =>
    request<{ ok: boolean }>(`/dashboards/${dashboardId}/drillthrough/${ruleId}`, {
      method: "DELETE",
    }),

  listFilterPresets: (dashboardId: string) =>
    request<Array<{ id: string; name: string; values: Record<string, unknown> }>>(
      `/dashboards/${dashboardId}/filter-presets`
    ),
  createFilterPreset: (dashboardId: string, name: string, values: Record<string, unknown>) =>
    request<{ id: string; name: string; values: Record<string, unknown> }>(
      `/dashboards/${dashboardId}/filter-presets`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, values }),
      }
    ),
  deleteFilterPreset: (dashboardId: string, presetId: string) =>
    request<{ ok: boolean }>(`/dashboards/${dashboardId}/filter-presets/${presetId}`, {
      method: "DELETE",
    }),

  distinctColumnValues: (datasetId: string, columnName: string) =>
    request<{ values: string[] }>(`/datasets/${datasetId}/columns/${encodeURIComponent(columnName)}/distinct`),

  filteredCount: (datasetId: string, extra_filters: FilterCondition[]) =>
    request<{ total_rows: number }>(`/datasets/${datasetId}/filtered-count`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filters: [], extra_filters }),
    }),

  generateInsights: (datasetId: string) =>
    request<{ dataset_id: string; insights: InsightItem[]; generated_at: string }>(
      `/datasets/${datasetId}/insights`,
      { method: "POST" }
    ),

  listChartTemplates: (datasetId?: string) =>
    request<ChartTemplate[]>(
      `/chart-studio/templates${datasetId ? `?dataset_id=${datasetId}` : ""}`
    ),
  saveChartTemplate: (body: {
    name: string;
    dataset_id: string;
    chart_type: string;
    config: Record<string, unknown>;
  }) =>
    request<ChartTemplate>("/chart-studio/templates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  listRelationships: () => request<Relationship[]>("/relationships"),
  detectRelationships: () =>
    request<Relationship[]>("/relationships/detect", { method: "POST" }),
  createRelationship: (body: Omit<Relationship, "id" | "created_at">) =>
    request<Relationship>("/relationships", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  relationshipGraph: () =>
    request<{ nodes: { id: string; label: string }[]; edges: unknown[] }>("/relationships/graph"),

  sqlStudioExecute: (dataset_id: string, query: string, page = 1, page_size = 500) =>
    request<SqlResult & { runtime_ms: number; success: boolean; error_message?: string | null }>(
      "/sql-studio/execute",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id, query, page, page_size }),
      }
    ),
  sqlStudioSchema: (datasetId: string) =>
    request<{ dataset_id: string; view_name: string; columns: ColumnInfo[] }>(
      `/sql-studio/schema/${datasetId}`
    ),
  listSavedQueries: () => request<SavedQuery[]>("/sql-studio/saved"),
  saveSqlQuery: (body: { name: string; dataset_id?: string; sql_text: string }) =>
    request<SavedQuery>("/sql-studio/saved", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  sqlQueryHistory: () => request<QueryHistoryEntry[]>("/sql-studio/history"),

  forecast: (
    datasetId: string,
    body: {
      date_column: string;
      value_column: string;
      horizon_days: number;
      method?: string;
      confidence_level?: number;
      seasonal_periods?: number;
      extra_filters?: FilterCondition[];
    }
  ) =>
    request<{
      points: ForecastPoint[];
      summary: string;
      method: string;
      horizon_days: number;
      seasonality_detected?: boolean;
      prediction_table?: Array<Record<string, unknown>>;
    }>(`/datasets/${datasetId}/forecast`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),

  detectAnomalies: (datasetId: string, extra_filters: FilterCondition[] = []) =>
    request<{ anomalies: Array<{ column: string; severity: string; explanation: string }>; summary: string }>(
      `/datasets/${datasetId}/anomalies`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ extra_filters }),
      }
    ),

  forecastExportCsv: async (
    datasetId: string,
    body: {
      date_column: string;
      value_column: string;
      horizon_days: number;
      method?: string;
      confidence_level?: number;
      extra_filters?: FilterCondition[];
    }
  ) => {
    const res = await fetch(`${getApiBase()}/datasets/${datasetId}/forecast/export/csv`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer demo-token",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.blob();
  },

  transformPreview: (
    datasetId: string,
    steps: Array<{ op: string; params: Record<string, unknown> }>,
    limit = 100
  ) =>
    request<{ columns: ColumnInfo[]; rows: Record<string, unknown>[]; row_count: number }>(
      `/datasets/${datasetId}/transform/preview`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ steps, limit }),
      }
    ),
};
