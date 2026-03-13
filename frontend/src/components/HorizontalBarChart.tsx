"use client";

import dynamic from "next/dynamic";
import type { ChartRow } from "@/lib/types";

// Plotly is browser-only; SSR must be disabled
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type MetricKey = "workers" | "wages" | "tasks";

interface Props {
  rows: ChartRow[];
  metric: MetricKey;
  color: string;
  subtitle: string;
}

const METRIC_CONFIG: Record<
  MetricKey,
  {
    title: string;
    col: keyof ChartRow;
    xLabel: string;
    unitScale: number;
    formatType: "number" | "currency_B" | "percent";
  }
> = {
  workers: {
    title: "Workers Affected",
    col: "workers_affected",
    xLabel: "Number of Workers Affected",
    unitScale: 1,
    formatType: "number",
  },
  wages: {
    title: "Wages Affected",
    col: "wages_affected",
    xLabel: "Annual Wages Affected ($B)",
    unitScale: 1e9,
    formatType: "currency_B",
  },
  tasks: {
    title: "% Tasks Affected",
    col: "pct_tasks_affected",
    xLabel: "% of Tasks Affected",
    unitScale: 1,
    formatType: "percent",
  },
};

function fmt(value: number, formatType: string): string {
  if (formatType === "number") return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (formatType === "currency_B") return `$${(value / 1e9).toFixed(2)}B`;
  if (formatType === "percent") return `${value.toFixed(1)}%`;
  return String(value);
}

function barLabel(
  value: number,
  total: number,
  formatType: string,
  unitScale: number
): string {
  if (formatType === "percent") return fmt(value, "percent");
  const share = total > 0 ? (value / total) * 100 : 0;
  return `${fmt(value, formatType)} (${share.toFixed(1)}%)`;
}

const GRID_COLOR = "rgba(200,200,200,0.35)";

export default function HorizontalBarChart({ rows, metric, color, subtitle }: Props) {
  const cfg = METRIC_CONFIG[metric];

  if (!rows || rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 bg-white rounded border border-gray-200">
        <span className="text-gray-400 text-sm">No data available</span>
      </div>
    );
  }

  const rawValues = rows.map((r) => r[cfg.col] as number);
  const plotValues = cfg.unitScale > 1
    ? rawValues.map((v) => v / cfg.unitScale)
    : rawValues;
  const categories = rows.map((r) => r.category);
  const total = rawValues.reduce((a, b) => a + b, 0);

  const labels = rawValues.map((v) => barLabel(v, total, cfg.formatType, cfg.unitScale));

  const hoverText = categories.map((cat, i) => {
    const raw = rawValues[i];
    const share = total > 0 ? (raw / total) * 100 : 0;
    return `<b>${cat}</b><br>${cfg.xLabel}: ${fmt(raw, cfg.formatType)}<br>Share of total: ${share.toFixed(1)}%`;
  });

  const n = rows.length;
  const height = Math.max(300, 32 * n + 140);

  return (
    <Plot
      data={[
        {
          type: "bar",
          orientation: "h",
          x: plotValues,
          y: categories,
          marker: { color, line: { width: 0 } },
          text: labels,
          textposition: "inside",
          insidetextanchor: "middle",
          textfont: { color: "white", size: 10, family: "Arial" },
          hovertext: hoverText,
          hoverinfo: "text",
          cliponaxis: false,
        },
      ]}
      layout={{
        title: {
          text: `<b>${cfg.title}</b><br><span style="font-size:11px;color:#777">${subtitle}</span>`,
          font: { size: 14, color: "#222" },
          x: 0,
          xanchor: "left",
          pad: { b: 4 },
        },
        xaxis: {
          title: { text: cfg.xLabel, font: { size: 11, color: "#555" } },
          showgrid: true,
          gridcolor: GRID_COLOR,
          gridwidth: 1,
          zeroline: true,
          zerolinecolor: "#ccc",
          tickfont: { size: 10, color: "#555" },
        },
        yaxis: {
          title: { text: "" },
          tickfont: { size: 10, color: "#333" },
          automargin: true,
        },
        height,
        margin: { l: 10, r: 30, t: 75, b: metric === "tasks" ? 80 : 30 },
        plot_bgcolor: "white",
        paper_bgcolor: "white",
        showlegend: false,
        bargap: 0.25,
        annotations:
          metric === "tasks"
            ? [
                {
                  text:
                    "Based on 2025 O*NET task data and 2024 BLS OEWS employment & wage data. " +
                    "Pct tasks affected = AI task comp / ECO task comp.",
                  xref: "paper",
                  yref: "paper",
                  x: 0,
                  y: -0.18,
                  showarrow: false,
                  font: { size: 8, color: "#888" },
                  align: "left",
                  xanchor: "left",
                },
              ]
            : [],
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}
