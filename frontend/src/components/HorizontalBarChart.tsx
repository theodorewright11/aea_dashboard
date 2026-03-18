"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, LabelList, ResponsiveContainer,
} from "recharts";
import type { ChartRow } from "@/lib/types";

type MetricKey = "workers" | "wages" | "tasks";

interface Props {
  rows: ChartRow[];
  metric: MetricKey;
  color: string;
}

const METRIC_CONFIG = {
  workers: {
    col:        "workers_affected" as keyof ChartRow,
    xLabel:     "Workers",
    unitScale:  1,
    formatType: "number",
  },
  wages: {
    col:        "wages_affected" as keyof ChartRow,
    xLabel:     "Annual Wages ($B)",
    unitScale:  1e9,
    formatType: "currency_B",
  },
  tasks: {
    col:        "pct_tasks_affected" as keyof ChartRow,
    xLabel:     "% Tasks Affected",
    unitScale:  1,
    formatType: "percent",
  },
} as const;

export function fmtChartValue(value: number, formatType: string): string {
  if (formatType === "number") {
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(0)}K`;
    return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }
  if (formatType === "currency_B") return `$${(value / 1e9).toFixed(2)}B`;
  if (formatType === "percent")    return `${value.toFixed(1)}%`;
  return String(value);
}

function truncate(s: string, max = 28): string {
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}

const CHART_FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

// ── Custom tooltip ────────────────────────────────────────────────────────────

function makeBarTooltip(formatType: string) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function BarTooltip({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const { category, rawValue } = payload[0].payload as { category: string; rawValue: number };
    return (
      <div style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: 7,
        padding: "8px 12px",
        fontSize: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.09)",
        maxWidth: 280,
      }}>
        <p style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 3, lineHeight: 1.4 }}>
          {category}
        </p>
        <p style={{ color: "var(--text-secondary)" }}>
          {fmtChartValue(rawValue, formatType)}
        </p>
      </div>
    );
  };
}

// ── Chart ─────────────────────────────────────────────────────────────────────

export default function HorizontalBarChart({ rows, metric, color }: Props) {
  const cfg = METRIC_CONFIG[metric];

  if (!rows || rows.length === 0) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        height: 120, fontSize: 13, color: "var(--text-muted)",
      }}>
        No data available
      </div>
    );
  }

  const data = rows.map((r) => ({
    category:  r.category,
    plotValue: cfg.unitScale > 1
      ? (r[cfg.col] as number) / cfg.unitScale
      : (r[cfg.col] as number),
    rawValue: r[cfg.col] as number,
  }));

  const n          = rows.length;
  const barSize    = 16;
  const rowPitch   = barSize + 18;
  const chartHeight = Math.max(180, n * rowPitch + 56);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 88, bottom: 24, left: 8 }}
        barCategoryGap="32%"
      >
        <CartesianGrid
          horizontal={false}
          stroke="rgba(0,0,0,0.05)"
          strokeDasharray="4 4"
        />

        <XAxis
          type="number"
          tickFormatter={(v: number) => fmtChartValue(
            v * (cfg.unitScale > 1 ? cfg.unitScale : 1),
            cfg.formatType,
          )}
          tick={{ fontSize: 10, fill: "#999", fontFamily: CHART_FONT }}
          axisLine={{ stroke: "rgba(0,0,0,0.07)" }}
          tickLine={false}
          label={{
            value:    cfg.xLabel,
            position: "insideBottom",
            offset:   -12,
            fontSize: 10,
            fill:     "#bbb",
            fontFamily: CHART_FONT,
          }}
        />

        <YAxis
          type="category"
          dataKey="category"
          tickFormatter={(v: string) => truncate(v, 28)}
          width={178}
          tick={{ fontSize: 11, fill: "#555", fontFamily: CHART_FONT }}
          axisLine={false}
          tickLine={false}
        />

        <Tooltip
          content={makeBarTooltip(cfg.formatType)}
          cursor={{ fill: "rgba(0,0,0,0.03)" }}
        />

        <Bar
          dataKey="plotValue"
          fill={color}
          radius={[0, 3, 3, 0]}
          maxBarSize={barSize}
        >
          <LabelList
            dataKey="rawValue"
            position="right"
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(v: any) => fmtChartValue(Number(v), cfg.formatType)}
            style={{ fontSize: 10, fill: "#888", fontFamily: CHART_FONT }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
