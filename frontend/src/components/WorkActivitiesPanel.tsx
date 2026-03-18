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
  groupId:       "A" | "B";
  color:         string;
  response:      WorkActivitiesResponse | null;
  loading:       boolean;
  error:         string | null;
  activityLevel: ActivityLevel;
  searchQuery:   string;
  contextSize:   number;
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
  title, downloadSlug, downloadTitle, accentColor, children,
}: {
  title: string; downloadSlug: string; downloadTitle: string;
  accentColor: string; children: React.ReactNode;
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
          onClick={() => downloadChartAsPng(containerRef.current, downloadSlug, { title: downloadTitle })}
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

function ActivityBarChart({
  rows, metric, color, matchedCategory,
}: {
  rows: ActivityRow[];
  metric: MetricKey;
  color: string;
  matchedCategory: string | null;
}) {
  const cfg = METRIC_CONFIG[metric];

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

  const data = rows.map((r) => ({
    category:  r.category,
    plotValue: cfg.unitScale > 1
      ? (r[cfg.col] as number) / cfg.unitScale
      : (r[cfg.col] as number),
    rawValue: r[cfg.col] as number,
  }));

  const n           = rows.length;
  const barSize     = 16;
  const rowPitch    = barSize + 18;
  const chartHeight = Math.max(180, n * rowPitch + 56);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function TooltipContent({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const { category, rawValue } = payload[0].payload as { category: string; rawValue: number };
    return (
      <div style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 8, padding: "10px 13px", fontSize: 12,
        boxShadow: "0 3px 12px rgba(0,0,0,0.11)", maxWidth: 280, minWidth: 180,
      }}>
        <p style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 6, lineHeight: 1.35 }}>
          {category}
        </p>
        <p style={{ fontWeight: 600, color: "var(--text-primary)" }}>
          {fmtChartValue(rawValue, cfg.formatType)}
        </p>
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
  activityLevel, searchQuery, contextSize,
}: Props) {
  const group    = response?.aei_group ?? response?.mcp_group ?? null;
  const allRows  = group?.[activityLevel] ?? [];
  const { rows, matchedCategory } = applySearch(allRows, searchQuery, contextSize);

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
            >
              <ActivityBarChart
                rows={rows}
                metric={metric}
                color={color}
                matchedCategory={matchedCategory}
              />
            </ChartCard>
          ))}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
