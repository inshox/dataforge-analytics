"""Pydantic request/response schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FilterOperator(str, Enum):
    equals = "equals"
    not_equals = "not_equals"
    contains = "contains"
    starts_with = "starts_with"
    greater_than = "greater_than"
    less_than = "less_than"
    greater_or_equal = "greater_or_equal"
    less_or_equal = "less_or_equal"
    between = "between"
    in_list = "in_list"
    is_empty = "is_empty"
    is_not_empty = "is_not_empty"


class FilterCondition(BaseModel):
    column: str
    operator: FilterOperator
    value: Any | None = None
    value_to: Any | None = None  # for between


class SortSpec(BaseModel):
    column: str
    descending: bool = False


class ColumnInfo(BaseModel):
    name: str
    dtype: str
    nullable: bool = True


class DatasetSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_filename: str | None = None
    source_format: str | None = None
    file_size_bytes: int | None = None
    row_count: int
    column_count: int
    columns: list[ColumnInfo] = Field(default_factory=list)
    status: str
    import_progress: int
    import_stage: str | None = None
    created_at: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    data_directory: str
    log_file: str
    duckdb: str
    polars: str
    polars_version: str | None = None
    duckdb_version: str | None = None
    host: str | None = None
    port: int | None = None


class ImportPreviewResponse(BaseModel):
    dataset_id: str
    preview_rows: list[dict[str, Any]]
    columns: list[ColumnInfo]
    row_count_estimate: int | None = None
    file_size_bytes: int
    detected_separator: str | None = None
    detected_encoding: str | None = None
    detected_format: str | None = None
    validation_warnings: list[str] = Field(default_factory=list)


class TopValue(BaseModel):
    value: str
    count: int


class ColumnProfile(BaseModel):
    column: str
    dtype: str
    inferred_type: str
    count: int
    null_count: int
    null_percent: float
    unique_count: int
    mean: float | None = None
    median: float | None = None
    min: float | None = None
    max: float | None = None
    std: float | None = None
    outlier_count: int = 0
    top_values: list[TopValue] = Field(default_factory=list)


class ColumnCorrelation(BaseModel):
    column_a: str
    column_b: str
    correlation: float


class DatasetProfileResponse(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    duplicate_rows: int
    columns: list[ColumnProfile]
    correlations: list[ColumnCorrelation] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)


class AiAnalystRequest(BaseModel):
    question: str


class AiAnalystResponse(BaseModel):
    sql: str
    explanation: str
    suggested_chart_type: str | None = None
    suggested_x_column: str | None = None
    suggested_y_column: str | None = None
    executive_summary: str | None = None
    data_quality_notes: list[str] = Field(default_factory=list)
    suggested_dashboard_layout: list[str] = Field(default_factory=list)


class AiAnalystExecuteRequest(BaseModel):
    sql: str
    page: int = 1
    page_size: int = 100


class ReportFormat(str, Enum):
    html = "html"
    pdf = "pdf"


class TableViewSpec(BaseModel):
    name: str
    filters: list[FilterCondition] = Field(default_factory=list)
    sort: list[SortSpec] = Field(default_factory=list)
    hidden_columns: list[str] = Field(default_factory=list)


class TableViewResponse(BaseModel):
    id: str
    name: str
    filters: list[FilterCondition]
    sort: list[SortSpec]
    hidden_columns: list[str]
    created_at: str | None = None


class RowsResponse(BaseModel):
    rows: list[dict[str, Any]]
    page: int
    page_size: int
    total_rows: int
    total_pages: int
    columns: list[ColumnInfo]


class ColumnStats(BaseModel):
    column: str
    dtype: str
    count: int
    null_count: int
    unique_count: int
    mean: float | None = None
    median: float | None = None
    min: float | None = None
    max: float | None = None
    std: float | None = None


class DatasetStatsResponse(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    duplicate_rows: int
    columns: list[ColumnStats]


class AggregateRequest(BaseModel):
    group_by: list[str] = Field(default_factory=list)
    aggregations: dict[str, str] = Field(default_factory=dict)  # column -> sum|mean|count|min|max|median
    extra_filters: list[FilterCondition] = Field(default_factory=list)


class AggregateResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict[str, Any]]


class ChartRequest(BaseModel):
    chart_type: str
    x_column: str
    y_column: str | None = None
    z_column: str | None = None
    source_column: str | None = None
    target_column: str | None = None
    parent_column: str | None = None
    aggregation: str = "count"
    filters: list[FilterCondition] = Field(default_factory=list)
    extra_filters: list[FilterCondition] = Field(default_factory=list)
    limit: int = 100
    config: dict[str, Any] = Field(default_factory=dict)


class ChartDataPoint(BaseModel):
    label: str
    value: float
    series: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ChartNode(BaseModel):
    id: str
    name: str
    value: float | None = None
    parent: str | None = None
    color: str | None = None


class ChartLink(BaseModel):
    source: str
    target: str
    value: float


class ChartResponse(BaseModel):
    chart_type: str
    data: list[ChartDataPoint]
    nodes: list[ChartNode] = Field(default_factory=list)
    links: list[ChartLink] = Field(default_factory=list)
    series: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class SqlRequest(BaseModel):
    query: str
    page: int = 1
    page_size: int = 100


class SqlResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    page: int
    page_size: int
    total_rows: int


# --- Enterprise v1.1 ---


class DashboardWidgetSpec(BaseModel):
    id: str | None = None
    widget_type: str
    dataset_id: str | None = None
    chart_type: str | None = None
    sql_query: str | None = None
    x: int = 0
    y: int = 0
    w: int = 4
    h: int = 3
    settings: dict[str, Any] = Field(default_factory=dict)


class DashboardCreate(BaseModel):
    name: str
    description: str | None = None


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    layout_json: str | None = None


class DashboardSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    widget_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class DashboardDetail(DashboardSummary):
    widgets: list[DashboardWidgetSpec] = Field(default_factory=list)
    layout_json: str | None = None


class DashboardSaveBody(BaseModel):
    name: str | None = None
    description: str | None = None
    layout_json: str | None = None
    widgets: list[DashboardWidgetSpec] = Field(default_factory=list)


class InsightItem(BaseModel):
    id: str
    category: str
    severity: str
    message: str
    metric: str | None = None
    value: float | None = None


class InsightsResponse(BaseModel):
    dataset_id: str
    insights: list[InsightItem]
    generated_at: str


class ChartTemplateCreate(BaseModel):
    name: str
    dataset_id: str
    chart_type: str
    config: dict[str, Any]


class ChartTemplateResponse(BaseModel):
    id: str
    name: str
    dataset_id: str
    chart_type: str
    config: dict[str, Any]
    created_at: str | None = None


class RelationshipSpec(BaseModel):
    left_dataset_id: str
    right_dataset_id: str
    left_column: str
    right_column: str
    relationship_type: str = "many_to_one"
    confidence: float = 1.0
    is_manual: bool = False


class RelationshipResponse(RelationshipSpec):
    id: str
    created_at: str | None = None


class SavedQueryCreate(BaseModel):
    name: str
    dataset_id: str | None = None
    sql_text: str


class SavedQueryResponse(BaseModel):
    id: str
    name: str
    dataset_id: str | None
    sql_text: str
    created_at: str | None = None
    updated_at: str | None = None


class QueryHistoryItem(BaseModel):
    id: str
    dataset_id: str | None
    sql_text: str
    runtime_ms: float
    rows_returned: int
    success: bool
    error_message: str | None = None
    created_at: str | None = None


class SqlExecuteRequest(BaseModel):
    dataset_id: str
    query: str
    page: int = 1
    page_size: int = 500


class SqlExecuteResponse(SqlResponse):
    runtime_ms: float
    success: bool
    error_message: str | None = None


class ForecastRequest(BaseModel):
    date_column: str
    value_column: str
    horizon_days: int = 30
    method: str = "linear"
    confidence_level: float = 0.95
    seasonal_periods: int | None = None
    extra_filters: list["FilterCondition"] = Field(default_factory=list)


class ForecastPoint(BaseModel):
    date: str
    value: float
    lower: float | None = None
    upper: float | None = None
    is_forecast: bool = False


class ForecastResponse(BaseModel):
    dataset_id: str
    method: str
    horizon_days: int
    points: list[ForecastPoint]
    summary: str
    seasonality_detected: bool = False
    prediction_table: list[dict[str, Any]] = Field(default_factory=list)


class WorkerJobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    progress: int
    error_message: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


class WorkerSubmitRequest(BaseModel):
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkerStatsResponse(BaseModel):
    active_jobs: int
    queued_jobs: int
    memory_mb: float | None = None
    cpu_percent: float | None = None


class WidgetVariableFilter(BaseModel):
    variable_id: str
    column: str
    operator: str = "eq"


class DashboardVariableCreate(BaseModel):
    name: str
    label: str | None = None
    type: str = "text"
    column_name: str | None = None
    dataset_id: str | None = None
    default_value: Any = None
    current_value: Any = None
    allowed_values: list[Any] = Field(default_factory=list)


class DashboardVariableUpdate(BaseModel):
    label: str | None = None
    type: str | None = None
    column_name: str | None = None
    dataset_id: str | None = None
    default_value: Any = None
    current_value: Any = None
    allowed_values: list[Any] | None = None


class DashboardVariableResponse(BaseModel):
    id: str
    dashboard_id: str
    name: str
    label: str
    type: str
    column_name: str | None = None
    dataset_id: str | None = None
    default_value: Any = None
    current_value: Any = None
    allowed_values: list[Any] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class DashboardFilterPresetCreate(BaseModel):
    name: str
    values: dict[str, Any] = Field(default_factory=dict)


class DashboardFilterPresetResponse(BaseModel):
    id: str
    dashboard_id: str
    name: str
    values: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class AnomalyDetectRequest(BaseModel):
    methods: list[str] = Field(default_factory=lambda: ["iqr", "zscore"])
    extra_filters: list["FilterCondition"] = Field(default_factory=list)


class TransformStep(BaseModel):
    op: str
    params: dict[str, Any] = Field(default_factory=dict)


class TransformPreviewRequest(BaseModel):
    steps: list[TransformStep]
    limit: int = 100


class TransformPreviewResponse(BaseModel):
    columns: list[ColumnInfo]
    rows: list[dict[str, Any]]
    row_count: int


class TransformPipelineCreate(BaseModel):
    name: str
    steps: list[TransformStep]


class TransformPipelineResponse(BaseModel):
    id: str
    dataset_id: str
    name: str
    steps: list[TransformStep]
    created_at: str | None = None


class DashboardDrillthroughCreate(BaseModel):
    source_widget_id: str | None = None
    target_dashboard_id: str
    trigger_column: str
    target_variable_name: str
    label: str | None = None
    open_mode: str = "tab"


class DashboardDrillthroughUpdate(BaseModel):
    source_widget_id: str | None = None
    target_dashboard_id: str | None = None
    trigger_column: str | None = None
    target_variable_name: str | None = None
    label: str | None = None
    open_mode: str | None = None


class DashboardDrillthroughResponse(BaseModel):
    id: str
    source_dashboard_id: str
    source_widget_id: str | None = None
    target_dashboard_id: str
    trigger_column: str
    target_variable_name: str
    label: str
    open_mode: str
    created_at: str | None = None


class FilteredCountRequest(BaseModel):
    filters: list[FilterCondition] = Field(default_factory=list)
    extra_filters: list[FilterCondition] = Field(default_factory=list)


class FilteredCountResponse(BaseModel):
    dataset_id: str
    total_rows: int


class DistinctValuesResponse(BaseModel):
    dataset_id: str
    column: str
    values: list[str]


class DashboardVariableSpec(BaseModel):
    name: str
    var_type: str = "string"
    value: Any = None


class DashboardTemplateSummary(BaseModel):
    id: str
    name: str
    category: str
    description: str
    widget_count: int


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    members: list[dict[str, Any]] = Field(default_factory=list)


class AnomalyItem(BaseModel):
    column: str
    row_index: int | None = None
    value: float | None = None
    date: str | None = None
    severity: str
    method: str
    explanation: str


class AnomaliesResponse(BaseModel):
    dataset_id: str
    anomalies: list[AnomalyItem]
    summary: str
