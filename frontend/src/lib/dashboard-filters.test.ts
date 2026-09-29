import { describe, expect, it } from "vitest";
import { buildDrillthroughHref, variableValuesToQuery } from "./dashboard-filters";

describe("dashboard-filters v1.4", () => {
  it("builds drill-through URL with variable param", () => {
    const href = buildDrillthroughHref("dash-2", "region", "Europe");
    expect(href).toContain("id=dash-2");
    expect(href).toContain("region=Europe");
  });

  it("serializes date range to query params", () => {
    const q = variableValuesToQuery({
      date_range: { from: "2025-01-01", to: "2025-12-31" },
      region: "North",
    });
    expect(q.date_range_from).toBe("2025-01-01");
    expect(q.date_range_to).toBe("2025-12-31");
    expect(q.region).toBe("North");
  });

  it("encodes multi-select as comma list", () => {
    const q = variableValuesToQuery({ tags: ["a", "b"] });
    expect(q.tags).toBe("a,b");
  });
});
