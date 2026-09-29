"use client";

import type { ChartLink, ChartNode } from "@/lib/api";

export function SankeyChart({
  nodes,
  links,
  width = 600,
  height = 320,
}: {
  nodes: ChartNode[];
  links: ChartLink[];
  width?: number;
  height?: number;
}) {
  if (!links.length) {
    return <p className="py-8 text-center text-sm text-forge-muted">No flow data</p>;
  }

  const nodeH = height / Math.max(nodes.length, 1);
  const yPos = new Map<string, number>();
  nodes.forEach((n, i) => yPos.set(n.id, i * nodeH + 20));
  const maxVal = Math.max(...links.map((l) => l.value), 1);

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} className="text-forge-text">
      {links.map((l, i) => {
        const y1 = yPos.get(l.source) ?? 0;
        const y2 = yPos.get(l.target) ?? 0;
        const strokeW = Math.max(2, (l.value / maxVal) * 24);
        return (
          <path
            key={i}
            d={`M ${width * 0.25} ${y1} C ${width * 0.5} ${y1}, ${width * 0.5} ${y2}, ${width * 0.75} ${y2}`}
            fill="none"
            stroke="var(--forge-text)"
            strokeOpacity={0.35}
            strokeWidth={strokeW}
          />
        );
      })}
      {nodes.map((n) => (
        <g key={n.id}>
          <rect
            x={width * 0.2}
            y={(yPos.get(n.id) ?? 0) - 8}
            width={12}
            height={16}
            fill="var(--forge-primary-bg)"
            rx={2}
          />
          <text x={width * 0.2 + 18} y={(yPos.get(n.id) ?? 0) + 4} fontSize={10} fill="var(--forge-muted)">
            {n.name}
          </text>
        </g>
      ))}
    </svg>
  );
}
