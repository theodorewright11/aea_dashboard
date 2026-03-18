"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, LabelList, ResponsiveContainer,
} from "recharts";
import type { GroupSettings, WorkActivitiesResponse, ActivityGroup, ActivityRow } from "@/lib/types";
import { fetchWorkActivities } from "@/lib/api";
import { downloadChartAsPng } from "@/lib/downloadChart";
import { fmtChartValue } from "./HorizontalBarChart";

type ActivityLevel  = "gwa" | "iwa" | "dwa";
type ActivityMetric = "workers" | "wages" | "tasks";

interface Props {
  groupId: "A" | "B";
  color: string;
  settings: GroupSettings;
}

const LEVEL_LABELS: Record<ActivityLevel, string> = {
  gwa: "General Work Activities",
  iwa: "Intermediate Work Activities",
  dwa: "Detailed Work Activities",
};

const CHART_FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

function truncate(s: string, max = 28): string {
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
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

// ── Activity chart (Recharts) ─────────────────────────────────────────────────

function ActivityChart({
  rows, color, metric,
}: {
  rows: ActivityRow[];
  color: string;
  metric: ActivityMetric;
}) {
  if (!rows.length) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        height: 100, fontSize: 12, color: "var(--text-muted)",
      }}>
        No data
      </div>
    );
  }

  type ColKey = "workers_affected" | "wages_affected" | "pct_tasks_affected";
  const metaMap: Record<ActivityMetric, { col: ColKey; xLabel: string; formatType: string; unitScale: number }> = {
    workers: { col: "workers_affected",   xLabel: "Workers",    formatType: "number",     unitScale: 1    },
    wages:   { col: "wages_affected",     xLabel: "Wages ($B)", formatType: "currency_B", unitScale: 1e9  },
    tasks:   { col: "pct_tasks_affected", xLabel: "% Tasks",    formatType: "percent",    unitScale: 1    },
  };
  const meta = metaMap[metric];

  const data = rows.map((r) => ({
    category:  r.category,
    plotValue: meta.unitScale > 1
      ? (r[meta.col] as number) / meta.unitScale
      : (r[meta.col] as number),
    rawValue: r[meta.col] as number,
  }));

  const n           = rows.length;
  const barSize     = 14;
  const chartHeight = Math.max(160, n * (barSize + 16) + 50);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function tooltipContent(p: any) {
    if (!p.active || !p.payload?.length) return null;
    const { category, rawValue } = p.payload[0].payload as { category: string; rawValue: number };
    return (
      <div style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: 7,
        padding: "8px 12px",
        fontSize: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.09)",
        maxWidth: 260,
      }}>
        <p style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 3, lineHeight: 1.4 }}>
          {category}
        </p>
        <p style={{ color: "var(--text-secondary)" }}>
          {fmtChartValue(rawValue, meta.formatType)}
        </p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 80, bottom: 20, left: 8 }}
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
            v * (meta.unitScale > 1 ? meta.unitScale : 1),
            meta.formatType,
          )}
          tick={{ fontSize: 10, fill: "#999", fontFamily: CHART_FONT }}
          axisLine={{ stroke: "rgba(0,0,0,0.07)" }}
          tickLine={false}
          label={{
            value: meta.xLabel,
            position: "insideBottom",
            offset: -10,
            fontSize: 10,
            fill: "#bbb",
            fontFamily: CHART_FONT,
          }}
        />
        <YAxis
          type="category"
          dataKey="category"
          tickFormatter={(v: string) => truncate(v, 28)}
          width={176}
          tick={{ fontSize: 11, fill: "#555", fontFamily: CHART_FONT }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={tooltipContent} cursor={{ fill: "rgba(0,0,0,0.03)" }} />
        <Bar dataKey="plotValue" fill={color} radius={[0, 3, 3, 0]} maxBarSize={barSize}>
          <LabelList
            dataKey="rawValue"
            position="right"
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(v: any) => fmtChartValue(Number(v), meta.formatType)}
            style={{ fontSize: 10, fill: "#888", fontFamily: CHART_FONT }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Activity group sub-panel ──────────────────────────────────────────────────

function ActivityGroupPanel({
  group, color, label,
}: {
  group: ActivityGroup;
  color: string;
  label: string;
}) {
  const [level,  setLevel]  = useState<ActivityLevel>("gwa");
  const [metric, setMetric] = useState<ActivityMetric>("workers");
  const chartRef = useRef<HTMLDivElement>(null);

  const rows = group[level] ?? [];

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderLeft: `3px solid ${color}`,
      borderRadius: 12,
      overflow: "hidden",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      {/* Sub-panel header */}
      <div style={{
        padding: "10px 14px 10px",
        borderBottom: "1px solid var(--border-light)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 8,
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", flex: 1, minWidth: 120 }}>
          {label}
        </span>

        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          {/* Level segmented control: GWA / IWA / DWA */}
          <div style={{
            display: "flex",
            border: "1px solid var(--border)",
            borderRadius: 6,
            overflow: "hidden",
          }}>
            {(["gwa", "iwa", "dwa"] as ActivityLevel[]).map((l, i) => (
              <button
                key={l}
                onClick={() => setLevel(l)}
                style={{
                  padding: "4px 9px",
                  fontSize: 11, fontWeight: level === l ? 700 : 400,
                  background: level === l ? color : "transparent",
                  color: level === l ? "white" : "var(--text-secondary)",
                  border: "none",
                  borderRight: i < 2 ? "1px solid var(--border)" : "none",
                  cursor: "pointer",
                  transition: "background 0.12s",
                }}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Metric segmented control: Workers / Wages / % Tasks */}
          <div style={{
            display: "flex",
            border: "1px solid var(--border)",
            borderRadius: 6,
            overflow: "hidden",
          }}>
            {([
              { key: "workers", label: "Workers" },
              { key: "wages",   label: "Wages"   },
              { key: "tasks",   label: "% Tasks" },
            ] as { key: ActivityMetric; label: string }[]).map((m, i) => (
              <button
                key={m.key}
                onClick={() => setMetric(m.key)}
                style={{
                  padding: "4px 9px",
                  fontSize: 11, fontWeight: metric === m.key ? 700 : 400,
                  background: metric === m.key ? "var(--brand-light)" : "transparent",
                  color: metric === m.key ? "var(--brand)" : "var(--text-secondary)",
                  border: "none",
                  borderRight: i < 2 ? "1px solid var(--border)" : "none",
                  cursor: "pointer",
                  transition: "background 0.12s",
                }}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Download button */}
          <button
            onClick={() => downloadChartAsPng(chartRef.current, `work-activities-${label.slice(0, 12)}-${level}-${metric}`)}
            title="Download chart as PNG"
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: "var(--text-muted)", padding: "4px",
              borderRadius: 4, display: "flex", alignItems: "center",
              transition: "color 0.12s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseOut={(e)  => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            <DownloadIcon />
          </button>
        </div>
      </div>

      {/* Level label */}
      <div style={{ padding: "6px 14px 2px", fontSize: 10, color: "var(--text-muted)" }}>
        {LEVEL_LABELS[level]}
      </div>

      {/* Chart */}
      <div ref={chartRef} style={{ padding: "0 8px 12px" }}>
        <ActivityChart rows={rows} color={color} metric={metric} />
      </div>
    </div>
  );
}

// ── WorkActivitiesPanel ───────────────────────────────────────────────────────

export default function WorkActivitiesPanel({ groupId, color, settings }: Props) {
  const [data, setData]       = useState<WorkActivitiesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!settings.selectedDatasets.length) { setData(null); return; }
    setLoading(true); setError(null);
    try {
      setData(await fetchWorkActivities(settings));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [settings]);

  useEffect(() => { load(); }, [load]);

  const hasAny = data && (data.aei_group || data.mcp_group);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, width: "100%", minWidth: 0 }}>
      {/* Group label — subtle accent */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 3, height: 18, borderRadius: 2, background: color, flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "-0.01em" }}>
          Group {groupId}
          {settings.selectedDatasets.length > 0 && (
            <span style={{ fontWeight: 400, color: "var(--text-muted)", marginLeft: 6 }}>
              · {settings.selectedDatasets.length === 1
                  ? settings.selectedDatasets[0]
                  : `${settings.selectedDatasets.length} datasets`}
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

      {error && (
        <div style={{ borderRadius: 8, border: "1px solid #fca5a5", background: "#fef2f2", padding: "12px 16px", fontSize: 13, color: "#b91c1c" }}>
          Error: {error}
        </div>
      )}

      {!loading && !error && !settings.selectedDatasets.length && (
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, padding: "32px", textAlign: "center", fontSize: 13, color: "var(--text-muted)" }}>
          Select at least one dataset to view work activity charts.
        </div>
      )}

      {!loading && !error && settings.selectedDatasets.length > 0 && !hasAny && data && (
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, padding: "32px", textAlign: "center", fontSize: 13, color: "var(--text-muted)" }}>
          No work activity data returned. The selected datasets may need the ECO 2015 baseline or crosswalk file.
        </div>
      )}

      {!loading && !error && data?.aei_group && (
        <ActivityGroupPanel
          group={data.aei_group}
          color={color}
          label={`AEI — ${data.aei_group.datasets.join(", ")} (ECO 2015 baseline)`}
        />
      )}
      {!loading && !error && data?.mcp_group && (
        <ActivityGroupPanel
          group={data.mcp_group}
          color={color}
          label={`MCP / Microsoft — ${data.mcp_group.datasets.join(", ")} (ECO 2025 baseline)`}
        />
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
