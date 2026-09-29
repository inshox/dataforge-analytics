/** Chart plugin registry — maps chart_type to metadata and component keys. */

export type ChartPlugin = {
  id: string;
  label: string;
  category: "standard" | "flow" | "finance" | "hierarchy";
  requiresSourceTarget?: boolean;
  requiresOHLC?: boolean;
  exportable: boolean;
};

export const CHART_REGISTRY: ChartPlugin[] = [
  { id: "bar", label: "Bar", category: "standard", exportable: true },
  { id: "line", label: "Line", category: "standard", exportable: true },
  { id: "area", label: "Area", category: "standard", exportable: true },
  { id: "pie", label: "Pie", category: "standard", exportable: true },
  { id: "scatter", label: "Scatter", category: "standard", exportable: true },
  { id: "bubble", label: "Bubble", category: "standard", exportable: true },
  { id: "histogram", label: "Histogram", category: "standard", exportable: true },
  { id: "heatmap", label: "Heatmap", category: "standard", exportable: true },
  { id: "boxplot", label: "Box Plot", category: "standard", exportable: true },
  { id: "radar", label: "Radar", category: "standard", exportable: true },
  { id: "sankey", label: "Sankey", category: "flow", requiresSourceTarget: true, exportable: true },
  { id: "funnel", label: "Funnel", category: "flow", exportable: true },
  { id: "network", label: "Network", category: "flow", requiresSourceTarget: true, exportable: true },
  { id: "candlestick", label: "Candlestick", category: "finance", requiresOHLC: true, exportable: true },
  { id: "waterfall", label: "Waterfall", category: "finance", exportable: true },
  { id: "treemap", label: "Treemap", category: "hierarchy", exportable: true },
  { id: "sunburst", label: "Sunburst", category: "hierarchy", exportable: true },
];

export function getChartPlugin(id: string): ChartPlugin | undefined {
  return CHART_REGISTRY.find((c) => c.id === id);
}
