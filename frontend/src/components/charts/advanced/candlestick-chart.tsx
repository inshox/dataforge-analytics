"use client";

type OhlcRow = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

export function CandlestickChart({ series }: { series: OhlcRow[] }) {
  if (!series.length) {
    return <p className="py-8 text-center text-sm text-forge-muted">No OHLC data</p>;
  }

  const w = 800;
  const h = 280;
  const pad = 40;
  const lows = series.map((s) => s.low);
  const highs = series.map((s) => s.high);
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const range = max - min || 1;
  const barW = Math.max(4, (w - pad * 2) / series.length - 2);

  const y = (v: number) => pad + ((max - v) / range) * (h - pad * 2);

  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`}>
      {series.map((c, i) => {
        const x = pad + i * (barW + 2);
        const up = c.close >= c.open;
        const color = up ? "#22c55e" : "#ef4444";
        return (
          <g key={c.date}>
            <line x1={x + barW / 2} y1={y(c.high)} x2={x + barW / 2} y2={y(c.low)} stroke={color} strokeWidth={1} />
            <rect
              x={x}
              y={y(Math.max(c.open, c.close))}
              width={barW}
              height={Math.max(2, Math.abs(y(c.open) - y(c.close)))}
              fill={color}
            />
          </g>
        );
      })}
    </svg>
  );
}
