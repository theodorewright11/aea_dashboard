"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, LabelList, ResponsiveContainer, Cell,
} from "recharts";
import type { ChartRow } from "@/lib/types";

type MetricKey = "workers" | "wages" | "tasks";

interface Props {
  rows: ChartRow[];
  metric: MetricKey;
  color: string;
  /** Total categories across the whole economy at this agg level */
  totalCategories?: number;
  /** Sum of workers_affected across ALL categories (for economy share) */
  totalEmp?: number;
  /** Sum of wages_affected across ALL categories (for economy share) */
  totalWages?: number;
  /** Other group's rows — for delta comparison in tooltip */
  otherGroupRows?: ChartRow[];
  /** Highlight this category (search match) */
  matchedCategory?: string | null;
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

function fmtDelta(delta: number, formatType: string): string {
  const sign = delta >= 0 ? "+" : "−";
  const abs  = Math.abs(delta);
  return `${sign}${fmtChartValue(abs, formatType)}`;
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function truncate(s: string, max = 28): string {
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}

const CHART_FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";
const MATCH_COLOR = "#c05621"; // highlight color for matched search bar

// ── Custom tooltip ────────────────────────────────────────────────────────────

interface TooltipPayloadItem {
  payload: ChartRow & {
    rawValue: number;
    workers_affected: number;
    wages_affected: number;
    pct_tasks_affected: number;
    rank_workers: number;
    rank_wages: number;
    rank_pct: number;
  };
}

function makeBarTooltip(
  metric: MetricKey,
  totalCategories: number,
  totalEmp: number,
  totalWages: number,
  otherGroupRows: ChartRow[],
) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function BarTooltip({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const item = (payload[0] as TooltipPayloadItem).payload;

    // Find matching row in other group
    const other = otherGroupRows.find((r) => r.category === item.category);

    const rows: { label: string; value: string; sub?: string; delta?: string }[] = [];

    // Workers
    {
      const v = item.workers_affected;
      const rank = item.rank_workers;
      const share = totalEmp > 0 ? (v / totalEmp * 100) : null;
      const otherV = other?.workers_affected;
      rows.push({
        label: "Workers",
        value: fmtChartValue(v, "number"),
        sub:   [
          rank > 0 && totalCategories > 0 ? `${ordinal(rank)} of ${totalCategories}` : null,
          share != null ? `${share.toFixed(1)}% of economy` : null,
        ].filter(Boolean).join(" · "),
        delta: otherV != null ? fmtDelta(v - otherV, "number") : undefined,
      });
    }

    // Wages
    {
      const v = item.wages_affected;
      const rank = item.rank_wages;
      const share = totalWages > 0 ? (v / totalWages * 100) : null;
      const otherV = other?.wages_affected;
      rows.push({
        label: "Wages",
        value: fmtChartValue(v, "currency_B"),
        sub:   [
          rank > 0 && totalCategories > 0 ? `${ordinal(rank)} of ${totalCategories}` : null,
          share != null ? `${share.toFixed(1)}% of economy` : null,
        ].filter(Boolean).join(" · "),
        delta: otherV != null ? fmtDelta(v - otherV, "currency_B") : undefined,
      });
    }

    // % Tasks
    {
      const v = item.pct_tasks_affected;
      const rank = item.rank_pct;
      const otherV = other?.pct_tasks_affected;
      rows.push({
        label: "% Tasks",
        value: fmtChartValue(v, "percent"),
        sub:   rank > 0 && totalCategories > 0
          ? `${ordinal(rank)} of ${totalCategories}`
          : undefined,
        delta: otherV != null ? fmtDelta(v - otherV, "percent") : undefined,
      });
    }

    return (
      <div style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "10px 13px",
        fontSize: 12,
        boxShadow: "0 3px 12px rgba(0,0,0,0.11)",
        maxWidth: 300,
        minWidth: 200,
      }}>
        <p style={{
          fontWeight: 700,
          color: "var(--text-primary)",
          marginBottom: 8,
          lineHeight: 1.35,
          fontSize: 12,
        }}>
          {item.category}
        </p>
        {rows.map((r) => (
          <div key={r.label} style={{ marginBottom: 5 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
              <span style={{ color: "var(--text-muted)", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {r.label}
              </span>
              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                {r.value}
              </span>
            </div>
            {r.sub && (
              <p style={{ fontSize: 10, color: "var(--text-muted)", margin: "1px 0 0" }}>{r.sub}</p>
            )}
            {r.delta !== undefined && (
              <p style={{
                fontSize: 10,
                margin: "1px 0 0",
                color: r.delta.startsWith("+") ? "#166534" : r.delta.startsWith("−") ? "#991b1b" : "var(--text-muted)",
                fontWeight: 500,
              }}>
                vs other group: {r.delta}
              </p>
            )}
          </div>
        ))}
      </div>
    );
  };
}

// ── Chart ─────────────────────────────────────────────────────────────────────

export default function HorizontalBarChart({
  rows,
  metric,
  color,
  totalCategories = 0,
  totalEmp = 0,
  totalWages = 0,
  otherGroupRows = [],
  matchedCategory = null,
}: Props) {
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
    category:          r.category,
    plotValue:         cfg.unitScale > 1
      ? (r[cfg.col] as number) / cfg.unitScale
      : (r[cfg.col] as number),
    rawValue:          r[cfg.col] as number,
    workers_affected:  r.workers_affected,
    wages_affected:    r.wages_affected,
    pct_tasks_affected: r.pct_tasks_affected,
    rank_workers:      r.rank_workers,
    rank_wages:        r.rank_wages,
    rank_pct:          r.rank_pct,
  }));

  const n           = rows.length;
  const barSize     = 16;
  const rowPitch    = barSize + 18;
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
          tick={({ x, y, payload }: { x: number; y: number; payload: { value: string } }) => {
            const isMatch = matchedCategory && payload.value === matchedCategory;
            return (
              <text
                x={x}
                y={y}
                dy={4}
                textAnchor="end"
                fontSize={11}
                fontWeight={isMatch ? 700 : 400}
                fill={isMatch ? MATCH_COLOR : "#555"}
                fontFamily={CHART_FONT}
              >
                {truncate(payload.value, 28)}
              </text>
            );
          }}
          axisLine={false}
          tickLine={false}
        />

        <Tooltip
          content={makeBarTooltip(metric, totalCategories, totalEmp, totalWages, otherGroupRows)}
          cursor={{ fill: "rgba(0,0,0,0.03)" }}
        />

        <Bar
          dataKey="plotValue"
          radius={[0, 3, 3, 0]}
          maxBarSize={barSize}
        >
          {data.map((entry) => {
            const isMatch = matchedCategory && entry.category === matchedCategory;
            return (
              <Cell
                key={entry.category}
                fill={isMatch ? MATCH_COLOR : color}
                opacity={matchedCategory && !isMatch ? 0.55 : 1}
              />
            );
          })}
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
