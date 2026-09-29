import { describe, expect, it } from "vitest";
import { CHART_REGISTRY, getChartPlugin } from "./registry";

describe("chart registry", () => {
  it("includes advanced chart types", () => {
    const ids = CHART_REGISTRY.map((c) => c.id);
    expect(ids).toContain("sankey");
    expect(ids).toContain("waterfall");
    expect(ids).toContain("candlestick");
  });

  it("resolves sankey plugin metadata", () => {
    const p = getChartPlugin("sankey");
    expect(p?.requiresSourceTarget).toBe(true);
    expect(p?.exportable).toBe(true);
  });
});
