"use client";

import { useRef } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, LabelList, ResponsiveContainer, Cell,
} from "recharts";
import type { WorkActivitiesResponse, ActivityRow } from "@/lib/types";
import { downloadChartAsPng } from "@/lib/downloadChart";
import { fmtChartValue } from "./HorizontalBarChart";

type ActivityLevel = "gwa" | "iwa" | "dwa";
type MetricKey     = "workers" | "wages" | "tasks";

interface Props {
  groupId:        "A" | "B";
  color:          string;
  response:       WorkActivitiesResponse | null;
  loading:        boolean;
  error:          string | null;
  activityLevel:  ActivityLevel;
  searchQuery:    string;
  contextSize:    number;
  /** Client-side topN slice applied before search */
  topN?:          number;
  /** Config summary lines shown as footer in downloaded PNGs */
  configSummary?: string[];
  /** Other group's response — for delta comparison in tooltip */
  otherResponse?: WorkActivitiesResponse | null;
  /** Other group's activity level — for looking up other group rows */
  otherActivityLevel?: ActivityLevel;
}

const LEVEL_LABELS: Record<ActivityLevel, string> = {
  gwa: "General Work Activities",
  iwa: "Intermediate Work Activities",
  dwa: "Detailed Work Activities",
};

const METRIC_TITLES: Record<MetricKey, string> = {
  workers: "Workers Affected",
  wages:   "Wages Affected",
  tasks:   "% Tasks Affected",
};

const METRIC_CONFIG = {
  workers: { col: "workers_affected"   as keyof ActivityRow, xLabel: "Workers",           formatType: "number",     unitScale: 1   },
  wages:   { col: "wages_affected"     as keyof ActivityRow, xLabel: "Annual Wages ($B)",  formatType: "currency_B", unitScale: 1e9 },
  tasks:   { col: "pct_tasks_affected" as keyof ActivityRow, xLabel: "% Tasks Affected",   formatType: "percent",    unitScale: 1   },
} as const;

const MATCH_COLOR = "#c05621";
const CHART_FONT  = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

function truncate(s: string, max = 28): string {
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}

function applySearch(
  rows: ActivityRow[],
  searchQuery: string,
  contextSize: number,
): { rows: ActivityRow[]; matchedCategory: string | null } {
  if (!searchQuery.trim()) return { rows, matchedCategory: null };
  const q   = searchQuery.toLowerCase().trim();
  const idx = rows.findIndex((r) => r.category.toLowerCase().includes(q));
  if (idx < 0) return { rows: [], matchedCategory: null };
  const matchedCategory = rows[idx].category;
  const start = Math.max(0, idx - contextSize);
  const end   = Math.min(rows.length, idx + contextSize + 1);
  return { rows: rows.slice(start, end), matchedCategory };
}

// ── Download icon ─────────────────────────────────────────────────────────────

function DownloadIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

// ── Chart card ────────────────────────────────────────────────────────────────

function ChartCard({
  title, downloadSlug, downloadTitle, accentColor, configLines, children,
}: {
  title: string; downloadSlug: string; downloadTitle: string;
  accentColor: string; configLines?: string[]; children: React.ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  return (
    <div style={{
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderLeft: `3px solid ${accentColor}`, borderRadius: 12,
      overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 18px 4px" }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
          {title}
        </span>
        <button
          onClick={() => downloadChartAsPng(containerRef.current, downloadSlug, { title: downloadTitle, configLines })}
          title={`Download ${title} as PNG`}
          style={{
            background: "none", border: "none", cursor: "pointer",
            color: "var(--text-muted)", padding: "4px",
            borderRadius: 4, display: "flex", alignItems: "center",
            transition: "color 0.12s",
          }}
          onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseOut={(e)  => (e.currentTarget.style.color = "var(--text-muted)")}
        ><DownloadIcon /></button>
      </div>
      <div ref={containerRef} style={{ padding: "0 12px 16px" }}>
        {children}
      </div>
    </div>
  );
}

// ── Bar chart ─────────────────────────────────────────────────────────────────

function fmtDelta(delta: number, formatType: string): string {
  const sign = delta >= 0 ? "+" : "\u2212";
  const abs  = Math.abs(delta);
  return `${sign}${fmtChartValue(abs, formatType)}`;
}

function fmtPctChange(thisV: number, otherV: number): string | null {
  if (otherV === 0) return null;
  const pct = ((thisV - otherV) / Math.abs(otherV)) * 100;
  const sign = pct >= 0 ? "+" : "\u2212";
  return `${sign}${Math.abs(pct).toFixed(1)}%`;
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function ActivityBarChart({
  rows, metric, color, matchedCategory,
  allRows, otherRows, totalEmp, totalWages, totalCategories,
}: {
  rows: ActivityRow[];
  metric: MetricKey;
  color: string;
  matchedCategory: string | null;
  /** Full row set (before topN/search) for rank computation */
  allRows: ActivityRow[];
  /** Other group's rows for delta in tooltip */
  otherRows: ActivityRow[];
  totalEmp: number;
  totalWages: number;
  totalCategories: number;
}) {
  const cfg = METRIC_CONFIG[metric];
  const hasOtherGroup = otherRows.length > 0;

  if (!rows.length) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        height: 120, fontSize: 13, color: "var(--text-muted)",
      }}>
        No data available
      </div>
    );
  }

  // Pre-compute rank maps from the full sorted row set
  const rankWorkers = new Map<string, number>();
  const rankWages = new Map<string, number>();
  const rankPct = new Map<string, number>();
  [...allRows].sort((a, b) => b.workers_affected - a.workers_affected).forEach((r, i) => rankWorkers.set(r.category, i + 1));
  [...allRows].sort((a, b) => b.wages_affected - a.wages_affected).forEach((r, i) => rankWages.set(r.category, i + 1));
  [...allRows].sort((a, b) => b.pct_tasks_affected - a.pct_tasks_affected).forEach((r, i) => rankPct.set(r.category, i + 1));

  // Build a lookup for full row data (all 3 metrics) for tooltip
  const rowLookup = new Map<string, ActivityRow>();
  allRows.forEach((r) => rowLookup.set(r.category, r));

  const data = rows.map((r) => ({
    category:  r.category,
    plotValue: cfg.unitScale > 1
      ? (r[cfg.col] as number) / cfg.unitScale
      : (r[cfg.col] as number),
    rawValue: r[cfg.col] as number,
    workers_affected: r.workers_affected,
    wages_affected: r.wages_affected,
    pct_tasks_affected: r.pct_tasks_affected,
  }));

  const n           = rows.length;
  const barSize     = 16;
  const rowPitch    = barSize + 18;
  const chartHeight = Math.max(180, n * rowPitch + 56);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function TooltipContent({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const item = payload[0].payload as { category: string; workers_affected: number; wages_affected: number; pct_tasks_affected: number };
    const other = hasOtherGroup ? otherRows.find((r) => r.category === item.category) : undefined;
    const notInOther = hasOtherGroup && other === undefined;

    type MetricRow = { label: string; value: string; sub?: string; delta?: string; pctChange?: string | null; absent?: boolean };
    const metricRows: MetricRow[] = [];

    // Workers
    {
      const v = item.workers_affected;
      const rank = rankWorkers.get(item.category) ?? 0;
      const share = totalEmp > 0 ? (v / totalEmp * 100) : null;
      const otherV = other?.workers_affected;
      metricRows.push({
        label: "Workers",
        value: fmtChartValue(v, "number"),
        sub: [
          rank > 0 && totalCategories > 0 ? `${ordinal(rank)} of ${totalCategories}` : null,
          share != null ? `${share.toFixed(1)}% of economy` : null,
        ].filter(Boolean).join(" \u00b7 "),
        delta: otherV != null ? fmtDelta(v - otherV, "number") : undefined,
        pctChange: otherV != null ? fmtPctChange(v, otherV) : undefined,
        absent: notInOther,
      });
    }

    // Wages
    {
      const v = item.wages_affected;
      const rank = rankWages.get(item.category) ?? 0;
      const share = totalWages > 0 ? (v / totalWages * 100) : null;
      const otherV = other?.wages_affected;
      metricRows.push({
        label: "Wages",
        value: fmtChartValue(v, "currency_B"),
        sub: [
          rank > 0 && totalCategories > 0 ? `${ordinal(rank)} of ${totalCategories}` : null,
          share != null ? `${share.toFixed(1)}% of economy` : null,
        ].filter(Boolean).join(" \u00b7 "),
        delta: otherV != null ? fmtDelta(v - otherV, "currency_B") : undefined,
        pctChange: otherV != null ? fmtPctChange(v, otherV) : undefined,
        absent: notInOther,
      });
    }

    // % Tasks
    {
      const v = item.pct_tasks_affected;
      const rank = rankPct.get(item.category) ?? 0;
      const otherV = other?.pct_tasks_affected;
      metricRows.push({
        label: "% Tasks",
        value: fmtChartValue(v, "percent"),
        sub: rank > 0 && totalCategories > 0 ? `${ordinal(rank)} of ${totalCategories}` : undefined,
        delta: otherV != null ? fmtDelta(v - otherV, "percent") : undefined,
        pctChange: otherV != null ? fmtPctChange(v, otherV) : undefined,
        absent: notInOther,
      });
    }

    return (
      <div style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 8, padding: "10px 13px", fontSize: 12,
        boxShadow: "0 3px 12px rgba(0,0,0,0.11)", maxWidth: 300, minWidth: 200,
      }}>
        <p style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 8, lineHeight: 1.35, fontSize: 12 }}>
          {item.category}
        </p>
        {metricRows.map((r) => (
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
            {r.absent && (
              <p style={{ fontSize: 10, margin: "1px 0 0", color: "var(--text-muted)", fontStyle: "italic" }}>
                not in other group
              </p>
            )}
            {r.delta !== undefined && (
              <p style={{
                fontSize: 10, margin: "1px 0 0",
                color: r.delta.startsWith("+") ? "#166534" : r.delta.startsWith("\u2212") ? "#991b1b" : "var(--text-muted)",
                fontWeight: 500,
              }}>
                vs other: {r.delta}{r.pctChange ? ` (${r.pctChange})` : ""}
              </p>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 88, bottom: 24, left: 8 }}
        barCategoryGap="32%"
      >
        <CartesianGrid horizontal={false} stroke="rgba(0,0,0,0.05)" strokeDasharray="4 4" />
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
            value: cfg.xLabel, position: "insideBottom", offset: -12,
            fontSize: 10, fill: "#bbb", fontFamily: CHART_FONT,
          }}
        />
        <YAxis
          type="category"
          dataKey="category"
          tickFormatter={(v: string) => truncate(v, 28)}
          width={178}
          tick={({ x, y, payload }: { x: string | number; y: string | number; payload: { value: string } }) => {
            const isMatch = matchedCategory && payload.value === matchedCategory;
            return (
              <text
                x={Number(x)} y={Number(y)} dy={4}
                textAnchor="end" fontSize={11}
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
        <Tooltip content={(p) => <TooltipContent {...p} />} cursor={{ fill: "rgba(0,0,0,0.03)" }} />
        <Bar dataKey="plotValue" radius={[0, 3, 3, 0]} maxBarSize={barSize}>
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

// ── WorkActivitiesPanel ───────────────────────────────────────────────────────

export default function WorkActivitiesPanel({
  groupId, color, response, loading, error,
  activityLevel, searchQuery, contextSize, topN, configSummary,
  otherResponse, otherActivityLevel,
}: Props) {
  const group    = response?.aei_group ?? response?.mcp_group ?? null;
  const rawRows  = group?.[activityLevel] ?? [];
  // Full rows for rank/totals (before topN/search)
  const fullRows = rawRows;
  // Apply topN client-side before search (backend may have returned all rows)
  const allRows  = topN != null ? rawRows.slice(0, topN) : rawRows;
  const { rows, matchedCategory } = applySearch(allRows, searchQuery, contextSize);

  // Other group's rows for delta comparison
  const otherGroup = otherResponse?.aei_group ?? otherResponse?.mcp_group ?? null;
  const otherLevel = otherActivityLevel ?? activityLevel;
  const otherRows  = otherGroup?.[otherLevel] ?? [];

  // Totals across all rows (for economy share %)
  const totalEmp   = fullRows.reduce((s, r) => s + r.workers_affected, 0);
  const totalWages = fullRows.reduce((s, r) => s + r.wages_affected, 0);
  const totalCategories = fullRows.length;

  const baselineLabel = response?.aei_group
    ? "ECO 2015 baseline"
    : response?.mcp_group
    ? "ECO 2025 baseline"
    : "";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, width: "100%", minWidth: 0 }}>
      {/* Group label */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 3, height: 18, borderRadius: 2, background: color, flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "-0.01em" }}>
          Group {groupId}
          {baselineLabel && (
            <span style={{ fontWeight: 400, color: "var(--text-muted)", fontSize: 12, marginLeft: 6 }}>
              · {baselineLabel}
            </span>
          )}
        </span>
      </div>

      {loading && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "48px 0" }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: `3px solid ${color}`, borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
          <span style={{ marginLeft: 10, fontSize: 13, color: "var(--text-muted)" }}>Computing…</span>
        </div>
      )}

      {!loading && error && (
        <div style={{ borderRadius: 8, border: "1px solid #fca5a5", background: "#fef2f2", padding: "12px 16px", fontSize: 13, color: "#b91c1c" }}>
          Error: {error}
        </div>
      )}

      {!loading && !error && response && !group && (
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, padding: "32px", textAlign: "center", fontSize: 13, color: "var(--text-muted)" }}>
          No work activity data returned. Check dataset and ECO baseline availability.
        </div>
      )}

      {!loading && !error && group && rows.length === 0 && (
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, padding: "32px", textAlign: "center", fontSize: 13, color: "var(--text-muted)" }}>
          {searchQuery
            ? `No match for "${searchQuery}" in ${LEVEL_LABELS[activityLevel]}.`
            : `No data for ${LEVEL_LABELS[activityLevel]}.`}
        </div>
      )}

      {!loading && !error && rows.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {(["workers", "wages", "tasks"] as MetricKey[]).map((metric) => (
            <ChartCard
              key={metric}
              title={METRIC_TITLES[metric]}
              downloadSlug={`wa-group-${groupId}-${activityLevel}-${metric}`}
              downloadTitle={`Group ${groupId} — ${LEVEL_LABELS[activityLevel]} — ${METRIC_TITLES[metric]}`}
              accentColor={color}
              configLines={configSummary}
            >
              <ActivityBarChart
                rows={rows}
                metric={metric}
                color={color}
                matchedCategory={matchedCategory}
                allRows={fullRows}
                otherRows={otherRows}
                totalEmp={totalEmp}
                totalWages={totalWages}
                totalCategories={totalCategories}
              />
            </ChartCard>
          ))}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
