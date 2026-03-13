"use client";

import dynamic from "next/dynamic";
import type { ChartRow } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type MetricKey = "workers" | "wages" | "tasks";

interface Props {
  rows: ChartRow[];
  metric: MetricKey;
  color: string;
  subtitle: string;
}

const METRIC_CONFIG = {
  workers: {
    title: "Workers Affected",
    col: "workers_affected" as keyof ChartRow,
    xLabel: "Number of Workers Affected",
    unitScale: 1,
    formatType: "number",
  },
  wages: {
    title: "Wages Affected",
    col: "wages_affected" as keyof ChartRow,
    xLabel: "Annual Wages Affected ($B)",
    unitScale: 1e9,
    formatType: "currency_B",
  },
  tasks: {
    title: "% Tasks Affected",
    col: "pct_tasks_affected" as keyof ChartRow,
    xLabel: "% of Tasks Affected",
    unitScale: 1,
    formatType: "percent",
  },
} as const;

function fmt(value: number, formatType: string): string {
  if (formatType === "number")     return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (formatType === "currency_B") return `$${(value / 1e9).toFixed(2)}B`;
  if (formatType === "percent")    return `${value.toFixed(1)}%`;
  return String(value);
}

function barLabel(value: number, total: number, formatType: string): string {
  if (formatType === "percent") return fmt(value, "percent");
  const share = total > 0 ? (value / total) * 100 : 0;
  return `${fmt(value, formatType)} (${share.toFixed(1)}%)`;
}

const GRID_COLOR = "rgba(200,200,200,0.3)";

export default function HorizontalBarChart({ rows, metric, color, subtitle }: Props) {
  const cfg = METRIC_CONFIG[metric];

  if (!rows || rows.length === 0) {
    return (
      <div
        className="flex items-center justify-center h-36"
        style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10 }}
      >
        <span style={{ color: "var(--text-muted)", fontSize: 13 }}>No data available</span>
      </div>
    );
  }

  const rawValues  = rows.map((r) => r[cfg.col] as number);
  const plotValues = cfg.unitScale > 1 ? rawValues.map((v) => v / cfg.unitScale) : rawValues;
  const categories = rows.map((r) => r.category);
  const total      = rawValues.reduce((a, b) => a + b, 0);
  const labels     = rawValues.map((v) => barLabel(v, total, cfg.formatType));

  const hoverText = categories.map((cat, i) => {
    const raw   = rawValues[i];
    const share = total > 0 ? (raw / total) * 100 : 0;
    return `<b>${cat}</b><br>${cfg.xLabel}: ${fmt(raw, cfg.formatType)}<br>Share of total: ${share.toFixed(1)}%`;
  });

  const n      = rows.length;
  const height = Math.max(280, 34 * n + 120);

  return (
    <Plot
      data={[
        {
          type:             "bar",
          orientation:      "h",
          x:                plotValues,
          y:                categories,
          marker:           { color, line: { width: 0 } },
          text:             labels,
          textposition:     "inside",
          insidetextanchor: "middle",
          textfont:         { color: "white", size: 10, family: "Inter, system-ui, sans-serif" },
          hovertext:        hoverText,
          hoverinfo:        "text",
          cliponaxis:       false,
        },
      ]}
      layout={{
        title: {
          text:    `<b>${cfg.title}</b><br><span style="font-size:11px;color:#888">${subtitle}</span>`,
          font:    { size: 14, color: "#1a1a1a", family: "Inter, system-ui, sans-serif" },
          x:       0,
          xanchor: "left",
          pad:     { b: 4 },
        },
        xaxis: {
          title:         { text: cfg.xLabel, font: { size: 11, color: "#666" } },
          showgrid:      true,
          gridcolor:     GRID_COLOR,
          gridwidth:     1,
          zeroline:      true,
          zerolinecolor: "#ddd",
          tickfont:      { size: 10, color: "#666" },
        },
        yaxis: {
          title:      { text: "" },
          tickfont:   { size: 10, color: "#333" },
          automargin: true,
        },
        height,
        margin:        { l: 10, r: 30, t: 70, b: 30 },
        plot_bgcolor:  "white",
        paper_bgcolor: "white",
        showlegend:    false,
        bargap:        0.28,
        annotations:   [],
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
