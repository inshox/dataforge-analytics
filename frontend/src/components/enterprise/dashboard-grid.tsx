"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { DashboardWidget } from "@/lib/api";
import type { Layout } from "react-grid-layout/legacy";

const GridLayout = dynamic(
  () =>
    import("react-grid-layout/legacy").then((mod) => {
      const { default: RGL, WidthProvider } = mod;
      return WidthProvider(RGL);
    }),
  { ssr: false }
);

export type DashboardGridProps = {
  widgets: DashboardWidget[];
  onLayoutChange: (widgets: DashboardWidget[]) => void;
  renderWidget: (widget: DashboardWidget) => React.ReactNode;
};

function toLayout(widgets: DashboardWidget[]): Layout {
  return widgets.map((w) => ({
    i: w.id || `w-${w.x}-${w.y}`,
    x: w.x,
    y: w.y,
    w: w.w,
    h: w.h,
    minW: 2,
    minH: 2,
  }));
}

export function DashboardGrid({ widgets, onLayoutChange, renderWidget }: DashboardGridProps) {
  const layout = useMemo(() => toLayout(widgets), [widgets]);

  return (
    <div className="dashboard-grid -mx-2">
      <GridLayout
        className="layout"
        layout={layout}
        cols={12}
        rowHeight={32}
        margin={[12, 12]}
        containerPadding={[8, 8]}
        draggableHandle=".widget-drag-handle"
        compactType="vertical"
        onLayoutChange={(next) => {
          const byId = new Map(widgets.map((w) => [w.id || `w-${w.x}-${w.y}`, w]));
          const updated = next
            .map((item) => {
              const w = byId.get(item.i);
              if (!w) return null;
              return { ...w, x: item.x, y: item.y, w: item.w, h: item.h };
            })
            .filter(Boolean) as DashboardWidget[];
          onLayoutChange(updated);
        }}
      >
        {widgets.map((w) => {
          const key = w.id || `w-${w.x}-${w.y}`;
          return (
            <div key={key} className="glass-panel overflow-hidden transition-shadow duration-200">
              {renderWidget(w)}
            </div>
          );
        })}
      </GridLayout>
    </div>
  );
}
