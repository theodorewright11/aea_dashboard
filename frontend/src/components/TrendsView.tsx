"use client";

import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import type {
  ConfigResponse, TrendsSettings, WATrendsSettings,
  TrendsResponse, TrendSeries,
} from "@/lib/types";
import { fetchTrends, fetchWATrends } from "@/lib/api";
import { downloadChartAsPng } from "@/lib/downloadChart";
import type { LegendItem } from "@/lib/downloadChart";

interface Props { config: ConfigResponse }

// ── Palettes ──────────────────────────────────────────────────────────────────

const PALETTE = [
  "#3a5f83", "#4a7c6f", "#c05621", "#7b5ea7",
  "#2d7d9a", "#6b8e23", "#b8860b", "#8b4513",
  "#4682b4", "#2e8b57", "#cd853f", "#708090",
  "#5b4e99", "#2d7a55", "#c45c29", "#3d6b9e",
];

const CAT_COLORS = [
  "#3a5f83", "#4a7c6f", "#c05621", "#7b5ea7",
  "#2d7d9a", "#6b8e23", "#b8860b", "#8b4513",
  "#4682b4", "#2e8b57", "#cd853f", "#708090",
];

// ── Dataset family helpers ─────────────────────────────────────────────────────

function isAEIFamily(name: string) { return name.startsWith("AEI"); }
function isMCPFamily(name: string) { return name.startsWith("MCP") || name === "Microsoft"; }

// ── Helpers ───────────────────────────────────────────────────────────────────

function getSeriesToFetch(
  selectedDatasets: string[],
  datasetSeries: Record<string, string[]>,
): string[] {
  const needed = new Set<string>();
  Object.entries(datasetSeries).forEach(([seriesName, datasets]) => {
    if (datasets.some((d) => selectedDatasets.includes(d))) needed.add(seriesName);
  });
  return Array.from(needed);
}

// ── Formatters ────────────────────────────────────────────────────────────────

type MetricKey = "workers_affected" | "wages_affected" | "pct_tasks_affected";
type LineMode  = "individual" | "average" | "max";
type SortMode  = "value" | "increase";
type IncMode   = "abs" | "pct";

const METRIC_OPTIONS: { key: MetricKey; label: string }[] = [
  { key: "workers_affected",   label: "Workers Affected"    },
  { key: "wages_affected",     label: "Wages Affected ($B)" },
  { key: "pct_tasks_affected", label: "% Tasks Affected"    },
];

const AGG_OPTIONS = [
  { value: "major"      as const, label: "Major"      },
  { value: "minor"      as const, label: "Minor"      },
  { value: "broad"      as const, label: "Broad"      },
  { value: "occupation" as const, label: "Occupation" },
];

function fmtVal(v: number, metric: MetricKey): string {
  if (metric === "workers_affected")   return v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : `${(v / 1e3).toFixed(0)}K`;
  if (metric === "wages_affected")     return `$${v.toFixed(2)}B`;
  if (metric === "pct_tasks_affected") return `${v.toFixed(1)}%`;
  return String(v);
}

function fmtIncrease(v: number, metric: MetricKey, mode: IncMode): string {
  if (mode === "pct") return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
  const prefix = v >= 0 ? "+" : "";
  return prefix + fmtVal(Math.abs(v), metric);
}

function fmtDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00Z");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[d.getUTCMonth()]} '${String(d.getUTCFullYear()).slice(2)}`;
}

const CHART_FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

// ── Data builders ─────────────────────────────────────────────────────────────

type LineConfig = { key: string; color: string };

function buildIndividualData(
  result: TrendsResponse,
  selectedDatasets: string[],
  shownCats: string[],
  metric: MetricKey,
): { chartData: Record<string, number | string>[]; lineConfigs: LineConfig[] } {
  const lookup = new Map<string, Map<string, Map<string, number>>>();

  result.series.forEach((s: TrendSeries) => {
    s.data_points
      .filter((dp) => selectedDatasets.includes(dp.dataset))
      .forEach((dp) => {
        if (!lookup.has(dp.dataset)) lookup.set(dp.dataset, new Map());
        const byDate = lookup.get(dp.dataset)!;
        if (!byDate.has(dp.date)) byDate.set(dp.date, new Map());
        const byCat = byDate.get(dp.date)!;
        dp.rows.forEach((r) => {
          const raw = r[metric] as number;
          byCat.set(r.category, metric === "wages_affected" ? raw / 1e9 : raw);
        });
      });
  });

  const dateSet = new Set<string>();
  lookup.forEach((byDate) => byDate.forEach((_, d) => dateSet.add(d)));
  const dates = Array.from(dateSet).sort();

  const lineConfigs: LineConfig[] = [];
  let colorIdx = 0;
  selectedDatasets.forEach((ds) => {
    if (!lookup.has(ds)) return;
    const byDate = lookup.get(ds)!;
    shownCats.forEach((cat) => {
      const hasData = dates.some((d) => byDate.get(d)?.has(cat));
      if (hasData) lineConfigs.push({ key: `${ds} — ${cat}`, color: PALETTE[colorIdx++ % PALETTE.length] });
    });
  });

  const chartData = dates.map((date) => {
    const point: Record<string, number | string> = { date };
    lineConfigs.forEach(({ key }) => {
      const sepIdx = key.indexOf(" — ");
      const ds  = key.slice(0, sepIdx);
      const cat = key.slice(sepIdx + 3);
      const v = lookup.get(ds)?.get(date)?.get(cat);
      if (v !== undefined) point[key] = v;
    });
    return point;
  });

  return { chartData, lineConfigs };
}

/**
 * Aggregate (average or cumulative-max) across selected datasets per category.
 * Max mode never decreases — running max is carried forward across dates.
 */
function buildAggregatedData(
  result: TrendsResponse,
  selectedDatasets: string[],
  shownCats: string[],
  metric: MetricKey,
  mode: "average" | "max",
): { chartData: Record<string, number | string>[]; lineConfigs: LineConfig[] } {
  const dateSet = new Set<string>();
  const lookup  = new Map<string, Map<string, number[]>>(); // date → cat → vals

  result.series.forEach((s: TrendSeries) => {
    s.data_points
      .filter((dp) => selectedDatasets.includes(dp.dataset))
      .forEach((dp) => {
        dateSet.add(dp.date);
        if (!lookup.has(dp.date)) lookup.set(dp.date, new Map());
        const byCat = lookup.get(dp.date)!;
        dp.rows.forEach((r) => {
          if (!shownCats.includes(r.category)) return;
          const raw = r[metric] as number;
          const v   = metric === "wages_affected" ? raw / 1e9 : raw;
          if (!byCat.has(r.category)) byCat.set(r.category, []);
          byCat.get(r.category)!.push(v);
        });
      });
  });

  const dates = Array.from(dateSet).sort();

  // Running max per category (only used in max mode)
  const runningMax = new Map<string, number>();

  const chartData = dates.map((date) => {
    const point: Record<string, number | string> = { date };
    const byCat = lookup.get(date);
    shownCats.forEach((cat) => {
      const vals = byCat?.get(cat);
      if (vals && vals.length > 0) {
        if (mode === "average") {
          point[cat] = vals.reduce((a, b) => a + b, 0) / vals.length;
        } else {
          const dateMax = Math.max(...vals);
          const prev    = runningMax.get(cat) ?? -Infinity;
          const cumulMax = Math.max(prev, dateMax);
          runningMax.set(cat, cumulMax);
          point[cat] = cumulMax;
        }
      } else if (mode === "max" && runningMax.has(cat)) {
        // Carry forward running max when no data at this date
        point[cat] = runningMax.get(cat)!;
      }
    });
    return point;
  });

  const lineConfigs = shownCats
    .map((cat, i) => ({ key: cat, color: CAT_COLORS[i % CAT_COLORS.length] }))
    .filter((lc) => chartData.some((p) => p[lc.key] !== undefined));

  return { chartData, lineConfigs };
}

/**
 * Compute increase (absolute or %) for each line key from first to last available data point.
 */
function computeIncreases(
  chartData: Record<string, number | string>[],
  lineConfigs: LineConfig[],
  _metric: MetricKey,
  incMode: IncMode,
): Map<string, number> {
  const increases = new Map<string, number>();
  lineConfigs.forEach(({ key }) => {
    const points = chartData.filter((p) => typeof p[key] === "number") as Record<string, number>[];
    if (points.length < 2) return;
    const first = points[0][key];
    const last  = points[points.length - 1][key];
    if (incMode === "abs") {
      increases.set(key, last - first);
    } else {
      if (first !== 0) increases.set(key, ((last - first) / Math.abs(first)) * 100);
    }
  });
  return increases;
}

/** Extract category name from a line key: "ds — cat" → "cat", "cat" → "cat" */
function catFromKey(key: string): string {
  const idx = key.indexOf(" — ");
  return idx >= 0 ? key.slice(idx + 3) : key;
}

/**
 * Compute a value score per category (max or avg across all data points).
 * Used for sort-by-value ordering.
 */
function computeCatValueScores(
  chartData: Record<string, number | string>[],
  lineConfigs: LineConfig[],
  mode: "max" | "avg",
): Map<string, number> {
  const acc = new Map<string, number[]>();
  chartData.forEach((pt) => {
    lineConfigs.forEach(({ key }) => {
      const v = pt[key];
      if (typeof v !== "number") return;
      const cat = catFromKey(key);
      if (!acc.has(cat)) acc.set(cat, []);
      acc.get(cat)!.push(v);
    });
  });
  const scores = new Map<string, number>();
  acc.forEach((vals, cat) => {
    scores.set(cat, mode === "max" ? Math.max(...vals) : vals.reduce((a, b) => a + b, 0) / vals.length);
  });
  return scores;
}

// ── UI components ─────────────────────────────────────────────────────────────

function ControlLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontSize: 10, fontWeight: 700, color: "var(--text-muted)",
      textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6,
    }}>{children}</p>
  );
}

function SegmentedControl<T extends string>({
  options, value, onChange, padding = "5px 11px",
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  padding?: string;
}) {
  return (
    <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
      {options.map(({ value: v, label }, i) => (
        <button
          key={v} onClick={() => onChange(v)}
          style={{
            padding, fontSize: 12,
            fontWeight: value === v ? 600 : 400,
            background: value === v ? "var(--brand-light)" : "transparent",
            color: value === v ? "var(--brand)" : "var(--text-secondary)",
            border: "none",
            borderRight: i < options.length - 1 ? "1px solid var(--border)" : "none",
            cursor: "pointer", transition: "background 0.12s", whiteSpace: "nowrap",
          }}
        >{label}</button>
      ))}
    </div>
  );
}

function DatasetPill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{
      fontSize: 11, padding: "4px 10px", borderRadius: 6,
      border: `1.5px solid ${active ? "var(--brand)" : "var(--border)"}`,
      background: active ? "var(--brand-light)" : "transparent",
      color: active ? "var(--brand)" : "var(--text-secondary)",
      cursor: "pointer", fontWeight: active ? 600 : 400,
      transition: "all 0.12s", whiteSpace: "nowrap",
    }}>{label}</button>
  );
}


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

// ── Section header ────────────────────────────────────────────────────────────

function SectionHead({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
      <p style={{
        fontSize: 12, fontWeight: 700, color: "var(--text-muted)",
        textTransform: "uppercase", letterSpacing: "0.09em",
        margin: 0, whiteSpace: "nowrap",
      }}>{label}</p>
      <div style={{ flex: 1, height: 1, background: "var(--border-light)" }} />
    </div>
  );
}

// ── Custom grid legend ────────────────────────────────────────────────────────

function ChartLegend({
  lineConfigs, increases, metric, incMode, lockedLine, setLockedLine,
}: {
  lineConfigs: LineConfig[];
  increases: Map<string, number> | null;
  metric: MetricKey;
  incMode: IncMode;
  lockedLine: string | null;
  setLockedLine: (k: string | null) => void;
}) {
  if (!lineConfigs.length) return null;
  return (
    <div style={{
      display: "flex", flexWrap: "wrap", gap: "3px 8px",
      padding: "10px 16px 4px",
      borderTop: "1px solid var(--border-light)",
    }}>
      {lineConfigs.map(({ key, color }) => {
        const inc     = increases?.get(key);
        const isLocked = lockedLine === key;
        const isDimmed = lockedLine != null && !isLocked;
        return (
          <button
            key={key}
            onClick={() => setLockedLine(isLocked ? null : key)}
            title={isLocked ? "Click to unlock" : "Click to lock focus"}
            style={{
              display: "flex", alignItems: "center", gap: 5,
              padding: "3px 7px", borderRadius: 5, cursor: "pointer",
              background: isLocked ? "var(--brand-light)" : "transparent",
              border: `1px solid ${isLocked ? "var(--brand)" : "transparent"}`,
              opacity: isDimmed ? 0.4 : 1,
              transition: "all 0.12s",
            }}
          >
            <span style={{
              width: 10, height: 3, borderRadius: 2,
              background: color, flexShrink: 0,
            }} />
            <span style={{
              fontSize: 11, color: "var(--text-secondary)",
              maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>{key}</span>
            {inc != null && (
              <span style={{
                fontSize: 10, fontWeight: 600, marginLeft: 2,
                color: inc >= 0 ? "#16a34a" : "#dc2626",
              }}>
                {fmtIncrease(inc, metric, incMode)}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

// ── Chart panel ───────────────────────────────────────────────────────────────

function ChartPanel({
  title, metric, chartData, lineConfigs, increases, incMode,
  loading, error, hasResult, lockedLine, setLockedLine, dateDatasets, catRanks,
}: {
  title: string; metric: MetricKey;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  chartData: Record<string, any>[];
  lineConfigs: LineConfig[];
  increases: Map<string, number> | null;
  incMode: IncMode;
  loading: boolean; error: string | null; hasResult: boolean;
  lockedLine: string | null;
  setLockedLine: (k: string | null) => void;
  dateDatasets?: Map<string, string[]>;
  catRanks?: Map<string, number>;
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [hoveredLine, setHoveredLine] = useState<string | null>(null);
  const [lockedPos, setLockedPos] = useState<{ x: number; y: number } | null>(null);
  const [lockedDate, setLockedDate] = useState<string | null>(null);

  const activeLine = lockedLine ?? hoveredLine;
  const chartHeight = Math.max(380, Math.min(lineConfigs.length, 14) * 22 + 180);

  // Build legendItems for download
  const downloadLegendItems = useMemo<LegendItem[]>(() => lineConfigs.map((lc) => {
    const inc = increases?.get(lc.key);
    return {
      color: lc.color,
      label: lc.key,
      extra: inc != null ? fmtIncrease(inc, metric, incMode) : undefined,
    };
  }), [lineConfigs, increases, metric, incMode]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function TrendsTooltip(props: any & { showAll?: boolean }) {
    if (!props.active || !props.payload?.length) return null;
    // When showAll is true (frozen panel), skip the activeLine filter — show everything
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filteredPayload = props.showAll
      ? props.payload
      : activeLine
        ? props.payload.filter((p: any) => p.dataKey === activeLine)
        : props.payload;
    const currentDate = props.label ?? "";

    // Helper: extract category name from a line key ("ds — cat" or just "cat")
    function catOf(key: string): string {
      const idx = key.indexOf(" — ");
      return idx >= 0 ? key.slice(idx + 3) : key;
    }

    // Index of hovered date in chartData (for looking up prev value)
    const dateIdx = chartData.findIndex((pt) => pt.date === currentDate);

    // Format a change: abs diff → uses metric format; pct diff → uses percent
    function fmtChange(absChange: number, baseVal: number): string {
      if (incMode === "pct") {
        if (baseVal === 0) return "—";
        const pct = (absChange / Math.abs(baseVal)) * 100;
        return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
      }
      return fmtIncrease(absChange, metric, "abs");
    }

    return (
      <div style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 8, padding: "10px 14px", fontSize: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.09)", maxWidth: 400,
        maxHeight: props.showAll ? undefined : "50vh", overflowY: props.showAll ? undefined : "auto",
      }}>
        <p style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
          {fmtDate(currentDate)}
        </p>
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {filteredPayload.map((p: any, i: number) => {
          const currentVal = p.value as number;
          const rank = catRanks?.get(catOf(p.dataKey as string));

          // Change from previous data point (scan backwards for last known value)
          let prevChange: number | null = null;
          let prevVal: number | null = null;
          if (dateIdx > 0) {
            for (let j = dateIdx - 1; j >= 0; j--) {
              const v = chartData[j][p.dataKey];
              if (typeof v === "number") { prevVal = v; prevChange = currentVal - v; break; }
            }
          }

          // Change from first data point for this line
          let fromStart: number | null = null;
          let firstVal: number | null = null;
          for (const pt of chartData) {
            const v = pt[p.dataKey];
            if (typeof v === "number") { firstVal = v; fromStart = currentVal - v; break; }
          }

          // Overall (start-to-end) increase from increases map
          const overallInc = increases?.get(p.dataKey);

          return (
            <div key={i} style={{
              marginBottom: i < filteredPayload.length - 1 ? 8 : 0,
              paddingBottom: i < filteredPayload.length - 1 ? 8 : 0,
              borderBottom: i < filteredPayload.length - 1 ? "1px solid var(--border-light)" : "none",
            }}>
              {/* Line name + rank */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8, marginBottom: 3 }}>
                <span style={{ color: p.color, fontWeight: 600, fontSize: 11, flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name}</span>
                {rank != null && (
                  <span style={{ fontSize: 10, color: "var(--text-muted)", whiteSpace: "nowrap" }}>#{rank}</span>
                )}
              </div>
              {/* Current value */}
              <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)", marginBottom: 4 }}>
                {fmtVal(currentVal, metric)}
              </div>
              {/* 3 interval changes */}
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {prevChange != null && prevVal != null && (
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>vs prev</span>
                    <span style={{ fontSize: 10, fontWeight: 600, color: prevChange >= 0 ? "#16a34a" : "#dc2626" }}>
                      {fmtChange(prevChange, prevVal)}
                    </span>
                  </div>
                )}
                {fromStart != null && firstVal != null && prevVal !== firstVal && (
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>from start</span>
                    <span style={{ fontSize: 10, fontWeight: 600, color: fromStart >= 0 ? "#16a34a" : "#dc2626" }}>
                      {fmtChange(fromStart, firstVal)}
                    </span>
                  </div>
                )}
                {overallInc != null && (
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>start→end</span>
                    <span style={{ fontSize: 10, fontWeight: 600, color: overallInc >= 0 ? "#16a34a" : "#dc2626" }}>
                      {fmtIncrease(overallInc, metric, incMode)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Close the frozen panel (used by dismiss button and outside-click)
  const dismissFrozen = useCallback(() => {
    setLockedLine(null); setLockedPos(null); setLockedDate(null);
  }, [setLockedLine]);

  // Click outside the frozen panel dismisses it
  useEffect(() => {
    if (!lockedPos) return;
    function onDocClick(e: MouseEvent) {
      const panel = document.getElementById("frozen-tooltip-panel");
      if (panel && panel.contains(e.target as Node)) return; // click inside panel
      dismissFrozen();
    }
    // Delay adding listener so the click that opened the panel doesn't immediately close it
    const timer = setTimeout(() => document.addEventListener("mousedown", onDocClick), 50);
    return () => { clearTimeout(timer); document.removeEventListener("mousedown", onDocClick); };
  }, [lockedPos, dismissFrozen]);

  // Build frozen tooltip content (memoized so it doesn't change on hover)
  const frozenContent = useMemo(() => {
    if (!lockedPos || !lockedDate || !lockedLine) return null;
    const pt = chartData.find((p) => p.date === lockedDate);
    if (!pt) return null;
    const payload: { dataKey: string; name: string; value: number; color: string }[] = [];
    lineConfigs.forEach((lc2) => {
      const v = pt[lc2.key];
      if (typeof v === "number") {
        payload.push({ dataKey: lc2.key, name: lc2.key, value: v, color: lc2.color });
      }
    });
    payload.sort((a, b) => b.value - a.value);
    return payload.length > 0 ? { payload, date: lockedDate, pos: lockedPos } : null;
  }, [lockedPos, lockedDate, lockedLine, chartData, lineConfigs]);

  return (
    <div
      style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 20px 8px" }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>{title}</span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            downloadChartAsPng(chartRef.current, `trends-${metric}`, { title, legendItems: downloadLegendItems });
          }}
          title="Download chart as PNG"
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "4px", borderRadius: 4, display: "flex", alignItems: "center", transition: "color 0.12s" }}
          onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseOut={(e)  => (e.currentTarget.style.color = "var(--text-muted)")}
        ><DownloadIcon /></button>
      </div>

      <div ref={chartRef} style={{ padding: "0 16px 4px" }}>
        {loading && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300 }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
            <span style={{ marginLeft: 10, fontSize: 13, color: "var(--text-muted)" }}>Computing trends…</span>
          </div>
        )}
        {!loading && error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#b91c1c", margin: "16px 0" }}>
            Error: {error}
          </div>
        )}
        {!loading && !error && !hasResult && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 280 }}>
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500, marginBottom: 4 }}>Select datasets and click Run to view trends</p>
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Tracks how metrics changed across dataset versions over time</p>
            </div>
          </div>
        )}
        {!loading && !error && hasResult && lineConfigs.length === 0 && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200, fontSize: 13, color: "var(--text-muted)" }}>
            No matching data for the selected configuration.
          </div>
        )}
        {!loading && !error && hasResult && lineConfigs.length > 0 && (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 30, bottom: 36, left: 60 }}
              onMouseLeave={() => { if (!lockedLine) setHoveredLine(null); }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              onClick={(state: any, event?: any) => {
                if (!state?.activeLabel) return;
                const date = state.activeLabel as string;
                // Determine which line to lock: use currently hovered/active, or first line with data
                const lineKey = hoveredLine ?? lineConfigs.find((lc) => {
                  const pt = chartData.find((p) => p.date === date);
                  return pt && typeof pt[lc.key] === "number";
                })?.key ?? null;
                if (!lineKey) return;

                // If clicking the same locked date+line, toggle off
                if (lockedLine === lineKey && lockedDate === date) {
                  dismissFrozen();
                  return;
                }

                // Get click position from the native event
                const nativeEvt = event?.nativeEvent ?? event;
                const cx = nativeEvt?.clientX ?? nativeEvt?.pageX;
                const cy = nativeEvt?.clientY ?? nativeEvt?.pageY;

                setLockedLine(lineKey);
                setLockedDate(date);
                if (cx != null && cy != null) setLockedPos({ x: cx, y: cy });
              }}
            >
              <CartesianGrid strokeDasharray="4 4" stroke="rgba(0,0,0,0.05)" vertical={false} />
              <XAxis
                dataKey="date"
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                tick={({ x, y, payload }: any) => {
                  const datasets = dateDatasets?.get(payload.value as string) ?? [];
                  const dsLabel  = datasets.join(", ");
                  const dateLabel = fmtDate(payload.value as string);
                  return (
                    <g>
                      {dsLabel && (
                        <text x={x} y={y} dy={10} textAnchor="middle"
                          fontSize={9} fill="#bbb" fontFamily={CHART_FONT}>{dsLabel}</text>
                      )}
                      <text x={x} y={y} dy={dsLabel ? 22 : 14} textAnchor="middle"
                        fontSize={11} fill="#888" fontFamily={CHART_FONT}>{dateLabel}</text>
                    </g>
                  );
                }}
                axisLine={{ stroke: "rgba(0,0,0,0.08)" }} tickLine={false}
              />
              <YAxis
                tickFormatter={(v: number) => fmtVal(v, metric)}
                tick={{ fontSize: 11, fill: "#888", fontFamily: CHART_FONT }}
                axisLine={false} tickLine={false} width={56}
              />
              {/* Hide Recharts hover tooltip when frozen panel is open */}
              {!lockedPos && <Tooltip content={(p) => <TrendsTooltip {...p} />} />}
              {lineConfigs.map((lc) => {
                const isActive = activeLine === lc.key;
                const isDimmed = activeLine != null && !isActive;
                return (
                  <Line
                    key={lc.key} type="monotone" dataKey={lc.key} stroke={lc.color}
                    strokeWidth={isDimmed ? 1.5 : isActive ? 4.5 : 3}
                    opacity={isDimmed ? 0.25 : 1}
                    dot={{ r: 4.5, strokeWidth: 0, fill: lc.color }}
                    activeDot={{ r: 7, strokeWidth: 2, stroke: "#fff" }}
                    connectNulls={false}
                    onMouseEnter={() => { if (!lockedLine) setHoveredLine(lc.key); }}
                    onMouseLeave={() => { if (!lockedLine) setHoveredLine(null); }}
                    className="recharts-line"
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Custom grid legend */}
      {!loading && !error && hasResult && lineConfigs.length > 0 && (
        <div data-legend-btn="true">
          <ChartLegend
            lineConfigs={lineConfigs}
            increases={increases}
            metric={metric}
            incMode={incMode}
            lockedLine={lockedLine}
            setLockedLine={setLockedLine}
          />
        </div>
      )}

      {/* Frozen tooltip — rendered via portal to document.body so it escapes overflow:hidden */}
      {frozenContent && typeof document !== "undefined" && (() => {
        const panelW = 380;
        const pad = 12;
        const winW = window.innerWidth;
        const winH = window.innerHeight;
        // Position: prefer right of click, flip left if it would overflow
        let left = frozenContent.pos.x + pad;
        if (left + panelW > winW - pad) left = Math.max(pad, frozenContent.pos.x - panelW - pad);
        // Vertical: prefer below click, but clamp to viewport
        let top = frozenContent.pos.y + pad;
        if (top > winH * 0.6) top = Math.max(pad, frozenContent.pos.y - winH * 0.4);
        // maxHeight = remaining space from top to bottom of viewport, with padding
        const maxH = winH - top - pad;
        return createPortal(
        <div
          id="frozen-tooltip-panel"
          style={{
            position: "fixed",
            top, left, width: panelW,
            zIndex: 99999,
            maxHeight: Math.max(200, maxH),
            overflowY: "auto",
            pointerEvents: "auto",
            borderRadius: 10,
            border: "1px solid var(--border)",
            boxShadow: "0 8px 30px rgba(0,0,0,0.18)",
            background: "var(--bg-surface)",
          }}
        >
          {/* Close button */}
          <div style={{ display: "flex", justifyContent: "flex-end", padding: "6px 8px 0" }}>
            <button
              onClick={dismissFrozen}
              style={{
                background: "var(--bg-surface)", border: "1px solid var(--border)",
                borderRadius: "50%", width: 22, height: 22,
                display: "flex", alignItems: "center", justifyContent: "center",
                cursor: "pointer", fontSize: 13, color: "var(--text-muted)",
              }}
              onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
              onMouseOut={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
            >×</button>
          </div>
          <TrendsTooltip active={true} payload={frozenContent.payload} label={frozenContent.date} showAll={true} />
        </div>,
        document.body,
      );
      })()}
    </div>
  );
}

// ── Shared controls sub-component ─────────────────────────────────────────────

function DatasetSelector({
  allDatasets, selectedDatasets, onToggle, onAll, onNone,
}: {
  allDatasets: string[];
  selectedDatasets: string[];
  onToggle: (ds: string) => void;
  onAll: () => void;
  onNone: () => void;
}) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <ControlLabel>Datasets Trends</ControlLabel>
        <button onClick={onAll}  style={{ fontSize: 10, color: "var(--brand)",      background: "none", border: "none", cursor: "pointer", padding: "0 2px", fontWeight: 600 }}>All</button>
        <button onClick={onNone} style={{ fontSize: 10, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: "0 2px" }}>None</button>
      </div>
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
        {allDatasets.map((ds) => (
          <DatasetPill key={ds} label={ds} active={selectedDatasets.includes(ds)} onClick={() => onToggle(ds)} />
        ))}
      </div>
    </div>
  );
}

// ── Family-aware dataset selector (Work Activity Trends) ─────────────────────

function DatasetSelectorWA({
  allDatasets, selectedDatasets, onToggle, onAll, onNone,
}: {
  allDatasets: string[];
  selectedDatasets: string[];
  onToggle: (ds: string) => void;
  onAll: () => void;
  onNone: () => void;
}) {
  const hasAEI = selectedDatasets.some(isAEIFamily);
  const hasMCP = selectedDatasets.some(isMCPFamily);
  const activeFamily: "aei" | "mcp" | null = hasAEI ? "aei" : hasMCP ? "mcp" : null;
  const canAll = activeFamily != null;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <ControlLabel>Datasets Trends</ControlLabel>
        <button
          disabled={!canAll}
          onClick={canAll ? onAll : undefined}
          style={{ fontSize: 10, color: canAll ? "var(--brand)" : "var(--text-muted)", background: "none", border: "none", cursor: canAll ? "pointer" : "default", padding: "0 2px", fontWeight: 600, opacity: canAll ? 1 : 0.4 }}
        >All</button>
        <button onClick={onNone} style={{ fontSize: 10, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: "0 2px" }}>None</button>
      </div>
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
        {allDatasets.map((ds) => {
          const hidden = activeFamily === "aei" ? isMCPFamily(ds) : activeFamily === "mcp" ? isAEIFamily(ds) : false;
          if (hidden) return null;
          return (
            <DatasetPill key={ds} label={ds} active={selectedDatasets.includes(ds)} onClick={() => onToggle(ds)} />
          );
        })}
      </div>
      {activeFamily && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", margin: "6px 0 0" }}>
          {activeFamily === "aei"
            ? "AEI selected — MCP/Microsoft hidden (different ECO baseline)"
            : "MCP/Microsoft selected — AEI hidden (different ECO baseline)"}
        </p>
      )}
    </div>
  );
}

// ── Occupation Trends tab ─────────────────────────────────────────────────────

function OccupationTrends({ config }: { config: ConfigResponse }) {
  const allDatasets = config.datasets ?? [];

  const [selectedDatasets, setSelectedDatasets] = useState<string[]>(allDatasets);
  const [lineMode,     setLineMode]     = useState<LineMode>("individual");
  const [metric,       setMetric]       = useState<MetricKey>("workers_affected");
  const [aggLevel,     setAggLevel]     = useState<"major" | "minor" | "broad" | "occupation">("major");
  const [method,       setMethod]       = useState<"freq" | "imp">("freq");
  const [geo,          setGeo]          = useState<"nat" | "ut">("nat");
  const [physicalMode, setPhysicalMode] = useState<"all" | "exclude" | "only">("all");
  const [topN,         setTopN]         = useState(8);
  const [useAutoAug,   setUseAutoAug]   = useState(false);
  const [useAdjMean,   setUseAdjMean]   = useState(false);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [result,       setResult]       = useState<TrendsResponse | null>(null);
  const [allCats,      setAllCats]      = useState<string[]>([]);

  // Sort / increase / value-agg options
  const [sortMode,      setSortMode]     = useState<SortMode>("value");
  const [incMode,       setIncMode]      = useState<IncMode>("abs");
  const [valueAggMode,  setValueAggMode] = useState<"max" | "avg">("max");

  // Search / context
  const [trendSearch,  setTrendSearch]  = useState("");
  const [ctxSize,      setCtxSize]      = useState(5);
  const searchFocused = useRef(false);

  // Lock state shared across the single chart panel
  const [lockedLine, setLockedLine] = useState<string | null>(null);

  const [panelCollapsed,    setPanelCollapsed]    = useState(false);

  const hasMCP = selectedDatasets.some((d) => d.startsWith("MCP") || d === "Microsoft");

  const run = useCallback(async () => {
    if (!selectedDatasets.length) return;
    setLoading(true); setError(null); setLockedLine(null);
    try {
      const seriesToFetch = getSeriesToFetch(selectedDatasets, config.dataset_series ?? {});
      if (!seriesToFetch.length) { setError("No valid series for selected datasets."); return; }
      // Fetch a larger pool so sort-by-increase can pick the true top N
      const fetchTopN = Math.max(topN, 50);
      const settings: TrendsSettings = {
        series: seriesToFetch, method, useAutoAug,
        useAdjMean: useAutoAug && useAdjMean,
        physicalMode, geo, aggLevel, topN: fetchTopN, sortBy: "Workers Affected",
      };
      const data = await fetchTrends(settings);
      setResult(data); setPanelCollapsed(true);
      const cats = new Set<string>();
      data.series.forEach((s: TrendSeries) => {
        s.data_points
          .filter((dp) => selectedDatasets.includes(dp.dataset))
          .forEach((dp) => dp.rows.forEach((r) => cats.add(r.category)));
      });
      setAllCats(Array.from(cats)); // store full pool; topN slice happens after sorting
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch trends");
    } finally { setLoading(false); }
  }, [selectedDatasets, aggLevel, method, geo, topN, useAutoAug, useAdjMean, physicalMode, config]);

  const metaLabel = METRIC_OPTIONS.find((m) => m.key === metric)?.label ?? "";

  const { chartData: rawChartData, lineConfigs: rawLineConfigs } = result
    ? lineMode === "individual"
      ? buildIndividualData(result, selectedDatasets, allCats, metric)
      : buildAggregatedData(result, selectedDatasets, allCats, metric, lineMode)
    : { chartData: [], lineConfigs: [] };

  // Compute increases for all lines
  const allIncreases = useMemo(
    () => rawLineConfigs.length > 0 ? computeIncreases(rawChartData, rawLineConfigs, metric, incMode) : null,
    [rawChartData, rawLineConfigs, metric, incMode],
  );

  // Value scores per category (max or avg across all data) — for sort-by-value
  const catValueScores = useMemo(
    () => rawLineConfigs.length > 0 ? computeCatValueScores(rawChartData, rawLineConfigs, valueAggMode) : new Map<string, number>(),
    [rawChartData, rawLineConfigs, valueAggMode],
  );

  // Full sorted pool (no topN slice) — used for search so categories beyond topN are reachable
  const sortedAllCats = useMemo(() => {
    if (sortMode === "increase" && allIncreases) {
      const getInc = (cat: string) => {
        let max = -Infinity;
        allIncreases.forEach((v, key) => {
          if (key === cat || key.endsWith(` — ${cat}`)) max = Math.max(max, v);
        });
        return max === -Infinity ? -Infinity : max;
      };
      return [...allCats].sort((a, b) => getInc(b) - getInc(a));
    }
    // Sort by value (max or avg across time range)
    return [...allCats].sort((a, b) => (catValueScores.get(b) ?? -Infinity) - (catValueScores.get(a) ?? -Infinity));
  }, [allCats, sortMode, allIncreases, catValueScores]);

  // Ranks based on full sorted pool (rank 1 = highest)
  const catRanks = useMemo(() => {
    const map = new Map<string, number>();
    sortedAllCats.forEach((cat, i) => map.set(cat, i + 1));
    return map;
  }, [sortedAllCats]);

  // Top-N slice for chart display when no search is active
  const sortedCats = useMemo(() => sortedAllCats.slice(0, topN), [sortedAllCats, topN]);

  // Search in full sorted pool so categories beyond topN can be found
  const shownCats = useMemo(() => {
    const q = trendSearch.trim().toLowerCase();
    if (!q) return sortedCats;
    const idx = sortedAllCats.findIndex((c) => c.toLowerCase().includes(q));
    if (idx < 0) return [];
    const start = Math.max(0, idx - ctxSize);
    const end   = Math.min(sortedAllCats.length, idx + ctxSize + 1);
    return sortedAllCats.slice(start, end);
  }, [sortedCats, sortedAllCats, trendSearch, ctxSize]);

  // Re-build chart data from shownCats
  const { chartData, lineConfigs } = result
    ? lineMode === "individual"
      ? buildIndividualData(result, selectedDatasets, shownCats, metric)
      : buildAggregatedData(result, selectedDatasets, shownCats, metric, lineMode)
    : { chartData: [], lineConfigs: [] };

  const increases = useMemo(
    () => lineConfigs.length > 0 ? computeIncreases(chartData, lineConfigs, metric, incMode) : null,
    [chartData, lineConfigs, metric, incMode],
  );

  // Build date → dataset name(s) map for x-axis labels
  const dateDatasets = useMemo(() => {
    if (!result) return undefined;
    const map = new Map<string, string[]>();
    result.series.forEach((s: TrendSeries) => {
      s.data_points
        .filter((dp) => selectedDatasets.includes(dp.dataset))
        .forEach((dp) => {
          if (!map.has(dp.date)) map.set(dp.date, []);
          if (!map.get(dp.date)!.includes(dp.dataset)) map.get(dp.date)!.push(dp.dataset);
        });
    });
    return map;
  }, [result, selectedDatasets]);

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

        {/* ── Collapsible settings ── */}
        {panelCollapsed ? (
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {selectedDatasets.length} dataset{selectedDatasets.length !== 1 ? "s" : ""} · {aggLevel} · {method === "freq" ? "Frequency" : "Importance"} · {geo === "nat" ? "National" : "Utah"}{useAutoAug ? " · Auto-aug" : ""}
            </span>
            <button
              onClick={() => setPanelCollapsed(false)}
              style={{ flexShrink: 0, padding: "3px 10px", fontSize: 11, background: "none", border: "1px solid var(--border)", borderRadius: 5, color: "var(--text-secondary)", cursor: "pointer" }}
            >▼ Settings</button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

            {/* Datasets */}
            <div>
              <SectionHead label="Datasets" />
              <DatasetSelector
                allDatasets={allDatasets} selectedDatasets={selectedDatasets}
                onToggle={(ds) => setSelectedDatasets((p) => p.includes(ds) ? p.filter((x) => x !== ds) : [...p, ds])}
                onAll={() => setSelectedDatasets(allDatasets)}
                onNone={() => setSelectedDatasets([])}
              />
            </div>

            {/* Display */}
            <div>
              <SectionHead label="Display" />
              <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
                <div>
                  <ControlLabel>Lines</ControlLabel>
                  <SegmentedControl
                    options={[
                      { value: "individual" as LineMode, label: "Individual" },
                      { value: "average"    as LineMode, label: "Average"    },
                      { value: "max"        as LineMode, label: "Max"        },
                    ]}
                    value={lineMode} onChange={setLineMode}
                  />
                </div>
                <div>
                  <ControlLabel>Metric</ControlLabel>
                  <SegmentedControl options={METRIC_OPTIONS.map((m) => ({ value: m.key, label: m.label }))} value={metric} onChange={setMetric} />
                </div>
                <div>
                  <ControlLabel>Aggregation</ControlLabel>
                  <SegmentedControl options={AGG_OPTIONS} value={aggLevel} onChange={setAggLevel} />
                </div>
                <div>
                  <ControlLabel>Geography</ControlLabel>
                  <SegmentedControl options={[{ value: "nat" as const, label: "National" }, { value: "ut" as const, label: "Utah" }]} value={geo} onChange={setGeo} />
                </div>
                <button onClick={run} className="btn-brand" style={{ padding: "9px 24px", fontSize: 13 }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
                  onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}>
                  Run
                </button>
              </div>
            </div>

            {/* Filtering */}
            <div>
              <SectionHead label="Filtering" />
              <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
                <div>
                  <ControlLabel>Method</ControlLabel>
                  <SegmentedControl options={[{ value: "freq" as const, label: "Frequency" }, { value: "imp" as const, label: "Importance" }]} value={method} onChange={setMethod} />
                </div>
                <div>
                  <ControlLabel>Physical tasks</ControlLabel>
                  <SegmentedControl
                    options={[{ value: "all" as const, label: "All" }, { value: "exclude" as const, label: "Non-physical" }, { value: "only" as const, label: "Physical only" }]}
                    value={physicalMode} onChange={setPhysicalMode}
                  />
                </div>
                <div>
                  <ControlLabel>Auto-aug</ControlLabel>
                  <SegmentedControl
                    options={[{ value: "off" as const, label: "Off" }, { value: "on" as const, label: "On" }]}
                    value={useAutoAug ? "on" : "off"}
                    onChange={(v) => setUseAutoAug(v === "on")}
                    padding="5px 7px"
                  />
                </div>
                {useAutoAug && hasMCP && (
                  <div>
                    <ControlLabel>Adj mean (MCP)</ControlLabel>
                    <SegmentedControl
                      options={[{ value: "off" as const, label: "Off" }, { value: "on" as const, label: "On" }]}
                      value={useAdjMean ? "on" : "off"}
                      onChange={(v) => setUseAdjMean(v === "on")}
                      padding="5px 7px"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Collapse button */}
            <button
              onClick={() => setPanelCollapsed(true)}
              style={{ alignSelf: "flex-start", marginTop: 4, padding: "3px 10px", fontSize: 11, background: "none", border: "1px solid var(--border)", borderRadius: 5, color: "var(--text-muted)", cursor: "pointer" }}
            >▲ Collapse</button>
          </div>
        )}

        {/* ── Always visible: Top N + (post-run) Sort + Search ── */}
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <ControlLabel>Top {topN}</ControlLabel>
            <input type="range" min={2} max={30} value={topN} onChange={(e) => setTopN(Number(e.target.value))}
              style={{ width: 96, accentColor: "var(--brand)", display: "block" }} />
          </div>
          <div>
            <ControlLabel>Sort</ControlLabel>
            <SegmentedControl
              options={[
                { value: "value"    as SortMode, label: "By value"    },
                { value: "increase" as SortMode, label: "By increase" },
              ]}
              value={sortMode} onChange={setSortMode}
            />
          </div>
          {sortMode === "value" && (
            <div>
              <ControlLabel>Value ranking</ControlLabel>
              <SegmentedControl
                options={[{ value: "max" as const, label: "Max" }, { value: "avg" as const, label: "Avg" }]}
                value={valueAggMode} onChange={setValueAggMode}
              />
            </div>
          )}
          {sortMode === "increase" && (
            <div>
              <ControlLabel>Increase type</ControlLabel>
              <SegmentedControl
                options={[{ value: "abs" as IncMode, label: "Absolute" }, { value: "pct" as IncMode, label: "% change" }]}
                value={incMode} onChange={setIncMode}
              />
            </div>
          )}
          <div>
            <ControlLabel>Search category</ControlLabel>
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              <input
                type="text" placeholder="Filter categories…" value={trendSearch}
                onChange={(e) => setTrendSearch(e.target.value)}
                onFocus={() => { searchFocused.current = true; }}
                onBlur={() => { searchFocused.current = false; }}
                style={{
                  fontSize: 12, border: "1px solid var(--border)", borderRadius: 6,
                  padding: "5px 26px 5px 8px", background: "var(--bg-surface)",
                  color: "var(--text-primary)", width: 160, height: 31, outline: "none",
                  transition: "border-color 0.15s",
                }}
                onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
                onMouseOut={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
              />
              {trendSearch && (
                <button onClick={() => setTrendSearch("")}
                  style={{ position: "absolute", right: 6, background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: 14, lineHeight: 1, padding: 0 }}>×</button>
              )}
            </div>
          </div>
          {trendSearch && (
            <div>
              <ControlLabel>Context ±</ControlLabel>
              <SegmentedControl
                options={[{ value: "3" as never, label: "3" }, { value: "5" as never, label: "5" }, { value: "10" as never, label: "10" }]}
                value={String(ctxSize) as never}
                onChange={(v) => setCtxSize(Number(v))}
              />
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <ChartPanel
          title={`${metaLabel} over time`} metric={metric}
          chartData={chartData} lineConfigs={lineConfigs}
          increases={increases}
          incMode={incMode}
          loading={loading} error={error} hasResult={!!result}
          lockedLine={lockedLine} setLockedLine={setLockedLine}
          dateDatasets={dateDatasets}
          catRanks={catRanks}
        />
      </div>
    </>
  );
}

// ── Work Activity Trends tab ──────────────────────────────────────────────────

function WorkActivityTrends({ config }: { config: ConfigResponse }) {
  const allDatasets = config.datasets ?? [];

  const [selectedDatasets, setSelectedDatasets] = useState<string[]>(allDatasets);
  const [lineMode,      setLineMode]      = useState<LineMode>("individual");
  const [activityLevel, setActivityLevel] = useState<"gwa" | "iwa" | "dwa">("gwa");
  const [metric,        setMetric]        = useState<MetricKey>("workers_affected");
  const [method,        setMethod]        = useState<"freq" | "imp">("freq");
  const [geo,           setGeo]           = useState<"nat" | "ut">("nat");
  const [physicalMode,  setPhysicalMode]  = useState<"all" | "exclude" | "only">("all");
  const [topN,          setTopN]          = useState(8);
  const [useAutoAug,    setUseAutoAug]    = useState(false);
  const [useAdjMean,    setUseAdjMean]    = useState(false);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState<string | null>(null);
  const [result,        setResult]        = useState<TrendsResponse | null>(null);
  const [allCats,       setAllCats]       = useState<string[]>([]);

  const [sortMode,      setSortMode]     = useState<SortMode>("value");
  const [incMode,       setIncMode]      = useState<IncMode>("abs");
  const [valueAggMode,  setValueAggMode] = useState<"max" | "avg">("max");
  const [trendSearch,   setTrendSearch]  = useState("");
  const [ctxSize,       setCtxSize]      = useState(5);
  const [lockedLine,    setLockedLine]   = useState<string | null>(null);

  const [panelCollapsed,    setPanelCollapsed]    = useState(false);

  const hasMCP = selectedDatasets.some((d) => d.startsWith("MCP") || d === "Microsoft");

  const run = useCallback(async () => {
    if (!selectedDatasets.length) return;
    setLoading(true); setError(null); setLockedLine(null);
    try {
      const seriesToFetch = getSeriesToFetch(selectedDatasets, config.dataset_series ?? {});
      if (!seriesToFetch.length) { setError("No valid series for selected datasets."); return; }
      const fetchTopN = Math.max(topN, 50);
      const settings: WATrendsSettings = {
        series: seriesToFetch, method, useAutoAug,
        useAdjMean: useAutoAug && useAdjMean,
        physicalMode, geo, topN: fetchTopN, sortBy: "Workers Affected", activityLevel,
      };
      const data = await fetchWATrends(settings);
      setResult(data); setPanelCollapsed(true);
      const cats = new Set<string>();
      data.series.forEach((s: TrendSeries) => {
        s.data_points
          .filter((dp) => selectedDatasets.includes(dp.dataset))
          .forEach((dp) => dp.rows.forEach((r) => cats.add(r.category)));
      });
      setAllCats(Array.from(cats));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch WA trends");
    } finally { setLoading(false); }
  }, [selectedDatasets, activityLevel, method, geo, topN, useAutoAug, useAdjMean, physicalMode, config]);

  const metaLabel = METRIC_OPTIONS.find((m) => m.key === metric)?.label ?? "";

  const { chartData: rawChartData, lineConfigs: rawLineConfigs } = result
    ? lineMode === "individual"
      ? buildIndividualData(result, selectedDatasets, allCats, metric)
      : buildAggregatedData(result, selectedDatasets, allCats, metric, lineMode)
    : { chartData: [], lineConfigs: [] };

  const allIncreases = useMemo(
    () => rawLineConfigs.length > 0 ? computeIncreases(rawChartData, rawLineConfigs, metric, incMode) : null,
    [rawChartData, rawLineConfigs, metric, incMode],
  );

  // Value scores per category for sort-by-value
  const catValueScores = useMemo(
    () => rawLineConfigs.length > 0 ? computeCatValueScores(rawChartData, rawLineConfigs, valueAggMode) : new Map<string, number>(),
    [rawChartData, rawLineConfigs, valueAggMode],
  );

  // Full sorted pool (no topN) — so search can find categories beyond topN
  const sortedAllCats = useMemo(() => {
    if (sortMode === "increase" && allIncreases) {
      const getInc = (cat: string) => {
        let max = -Infinity;
        allIncreases.forEach((v, key) => {
          if (key === cat || key.endsWith(` — ${cat}`)) max = Math.max(max, v);
        });
        return max === -Infinity ? -Infinity : max;
      };
      return [...allCats].sort((a, b) => getInc(b) - getInc(a));
    }
    return [...allCats].sort((a, b) => (catValueScores.get(b) ?? -Infinity) - (catValueScores.get(a) ?? -Infinity));
  }, [allCats, sortMode, allIncreases, catValueScores]);

  const catRanks = useMemo(() => {
    const map = new Map<string, number>();
    sortedAllCats.forEach((cat, i) => map.set(cat, i + 1));
    return map;
  }, [sortedAllCats]);

  const sortedCats = useMemo(() => sortedAllCats.slice(0, topN), [sortedAllCats, topN]);

  const shownCats = useMemo(() => {
    const q = trendSearch.trim().toLowerCase();
    if (!q) return sortedCats;
    const idx = sortedAllCats.findIndex((c) => c.toLowerCase().includes(q));
    if (idx < 0) return [];
    const start = Math.max(0, idx - ctxSize);
    const end   = Math.min(sortedAllCats.length, idx + ctxSize + 1);
    return sortedAllCats.slice(start, end);
  }, [sortedCats, sortedAllCats, trendSearch, ctxSize]);

  const { chartData, lineConfigs } = result
    ? lineMode === "individual"
      ? buildIndividualData(result, selectedDatasets, shownCats, metric)
      : buildAggregatedData(result, selectedDatasets, shownCats, metric, lineMode)
    : { chartData: [], lineConfigs: [] };

  const increases = useMemo(
    () => lineConfigs.length > 0 ? computeIncreases(chartData, lineConfigs, metric, incMode) : null,
    [chartData, lineConfigs, metric, incMode],
  );

  // Build date → dataset name(s) map for x-axis labels
  const dateDatasets = useMemo(() => {
    if (!result) return undefined;
    const map = new Map<string, string[]>();
    result.series.forEach((s: TrendSeries) => {
      s.data_points
        .filter((dp) => selectedDatasets.includes(dp.dataset))
        .forEach((dp) => {
          if (!map.has(dp.date)) map.set(dp.date, []);
          if (!map.get(dp.date)!.includes(dp.dataset)) map.get(dp.date)!.push(dp.dataset);
        });
    });
    return map;
  }, [result, selectedDatasets]);

  const levelLabels: Record<string, string> = {
    gwa: "General Work Activities", iwa: "Intermediate Work Activities", dwa: "Detailed Work Activities",
  };

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

        {/* ── Collapsible settings ── */}
        {panelCollapsed ? (
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {selectedDatasets.length} dataset{selectedDatasets.length !== 1 ? "s" : ""} · {levelLabels[activityLevel]} · {method === "freq" ? "Frequency" : "Importance"} · {geo === "nat" ? "National" : "Utah"}{useAutoAug ? " · Auto-aug" : ""}
            </span>
            <button
              onClick={() => setPanelCollapsed(false)}
              style={{ flexShrink: 0, padding: "3px 10px", fontSize: 11, background: "none", border: "1px solid var(--border)", borderRadius: 5, color: "var(--text-secondary)", cursor: "pointer" }}
            >▼ Settings</button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

            {/* Datasets */}
            <div>
              <SectionHead label="Datasets" />
              <DatasetSelectorWA
                allDatasets={allDatasets} selectedDatasets={selectedDatasets}
                onToggle={(ds) => setSelectedDatasets((p) => p.includes(ds) ? p.filter((x) => x !== ds) : [...p, ds])}
                onAll={() => {
                  const hasAEI = selectedDatasets.some(isAEIFamily);
                  setSelectedDatasets(allDatasets.filter(hasAEI ? isAEIFamily : isMCPFamily));
                }}
                onNone={() => setSelectedDatasets([])}
              />
            </div>

            {/* Display */}
            <div>
              <SectionHead label="Display" />
              <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
                <div>
                  <ControlLabel>Lines</ControlLabel>
                  <SegmentedControl
                    options={[
                      { value: "individual" as LineMode, label: "Individual" },
                      { value: "average"    as LineMode, label: "Average"    },
                      { value: "max"        as LineMode, label: "Max"        },
                    ]}
                    value={lineMode} onChange={setLineMode}
                  />
                </div>
                <div>
                  <ControlLabel>Activity level</ControlLabel>
                  <SegmentedControl
                    options={[{ value: "gwa" as const, label: "GWA" }, { value: "iwa" as const, label: "IWA" }, { value: "dwa" as const, label: "DWA" }]}
                    value={activityLevel} onChange={setActivityLevel}
                  />
                </div>
                <div>
                  <ControlLabel>Metric</ControlLabel>
                  <SegmentedControl options={METRIC_OPTIONS.map((m) => ({ value: m.key, label: m.label }))} value={metric} onChange={setMetric} />
                </div>
                <div>
                  <ControlLabel>Geography</ControlLabel>
                  <SegmentedControl options={[{ value: "nat" as const, label: "National" }, { value: "ut" as const, label: "Utah" }]} value={geo} onChange={setGeo} />
                </div>
                <button onClick={run} className="btn-brand" style={{ padding: "9px 24px", fontSize: 13 }}
                  onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
                  onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}>
                  Run
                </button>
              </div>
            </div>

            {/* Filtering */}
            <div>
              <SectionHead label="Filtering" />
              <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
                <div>
                  <ControlLabel>Method</ControlLabel>
                  <SegmentedControl options={[{ value: "freq" as const, label: "Frequency" }, { value: "imp" as const, label: "Importance" }]} value={method} onChange={setMethod} />
                </div>
                <div>
                  <ControlLabel>Physical tasks</ControlLabel>
                  <SegmentedControl
                    options={[{ value: "all" as const, label: "All" }, { value: "exclude" as const, label: "Non-physical" }, { value: "only" as const, label: "Physical only" }]}
                    value={physicalMode} onChange={setPhysicalMode}
                  />
                </div>
                <div>
                  <ControlLabel>Auto-aug</ControlLabel>
                  <SegmentedControl
                    options={[{ value: "off" as const, label: "Off" }, { value: "on" as const, label: "On" }]}
                    value={useAutoAug ? "on" : "off"}
                    onChange={(v) => setUseAutoAug(v === "on")}
                    padding="5px 7px"
                  />
                </div>
                {useAutoAug && hasMCP && (
                  <div>
                    <ControlLabel>Adj mean (MCP)</ControlLabel>
                    <SegmentedControl
                      options={[{ value: "off" as const, label: "Off" }, { value: "on" as const, label: "On" }]}
                      value={useAdjMean ? "on" : "off"}
                      onChange={(v) => setUseAdjMean(v === "on")}
                      padding="5px 7px"
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Collapse button */}
            <button
              onClick={() => setPanelCollapsed(true)}
              style={{ alignSelf: "flex-start", marginTop: 4, padding: "3px 10px", fontSize: 11, background: "none", border: "1px solid var(--border)", borderRadius: 5, color: "var(--text-muted)", cursor: "pointer" }}
            >▲ Collapse</button>
          </div>
        )}

        {/* ── Always visible: Top N + (post-run) Sort + Search ── */}
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <ControlLabel>Top {topN}</ControlLabel>
            <input type="range" min={2} max={30} value={topN} onChange={(e) => setTopN(Number(e.target.value))}
              style={{ width: 96, accentColor: "var(--brand)", display: "block" }} />
          </div>
          <div>
            <ControlLabel>Sort</ControlLabel>
            <SegmentedControl
              options={[{ value: "value" as SortMode, label: "By value" }, { value: "increase" as SortMode, label: "By increase" }]}
              value={sortMode} onChange={setSortMode}
            />
          </div>
          {sortMode === "value" && (
            <div>
              <ControlLabel>Value ranking</ControlLabel>
              <SegmentedControl
                options={[{ value: "max" as const, label: "Max" }, { value: "avg" as const, label: "Avg" }]}
                value={valueAggMode} onChange={setValueAggMode}
              />
            </div>
          )}
          {sortMode === "increase" && (
            <div>
              <ControlLabel>Increase type</ControlLabel>
              <SegmentedControl
                options={[{ value: "abs" as IncMode, label: "Absolute" }, { value: "pct" as IncMode, label: "% change" }]}
                value={incMode} onChange={setIncMode}
              />
            </div>
          )}
          <div>
            <ControlLabel>Search category</ControlLabel>
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              <input
                type="text" placeholder="Filter categories…" value={trendSearch}
                onChange={(e) => setTrendSearch(e.target.value)}
                style={{
                  fontSize: 12, border: "1px solid var(--border)", borderRadius: 6,
                  padding: "5px 26px 5px 8px", background: "var(--bg-surface)",
                  color: "var(--text-primary)", width: 160, height: 31, outline: "none",
                  transition: "border-color 0.15s",
                }}
                onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
                onMouseOut={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
              />
              {trendSearch && (
                <button onClick={() => setTrendSearch("")}
                  style={{ position: "absolute", right: 6, background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: 14, lineHeight: 1, padding: 0 }}>×</button>
              )}
            </div>
          </div>
          {trendSearch && (
            <div>
              <ControlLabel>Context ±</ControlLabel>
              <SegmentedControl
                options={[{ value: "3" as never, label: "3" }, { value: "5" as never, label: "5" }, { value: "10" as never, label: "10" }]}
                value={String(ctxSize) as never}
                onChange={(v) => setCtxSize(Number(v))}
              />
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <ChartPanel
          title={`${levelLabels[activityLevel]} — ${metaLabel} over time`} metric={metric}
          chartData={chartData} lineConfigs={lineConfigs}
          increases={increases}
          incMode={incMode}
          loading={loading} error={error} hasResult={!!result}
          lockedLine={lockedLine} setLockedLine={setLockedLine}
          dateDatasets={dateDatasets}
          catRanks={catRanks}
        />
      </div>
    </>
  );
}

// ── Main TrendsView ───────────────────────────────────────────────────────────

export default function TrendsView({ config }: Props) {
  const [activeTab, setActiveTab] = useState<"occupation" | "work-activities">("occupation");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - var(--nav-height))", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ background: "var(--bg-header)", borderBottom: "1px solid var(--border)", padding: "18px 24px 16px", flexShrink: 0 }}>
        <div style={{ marginBottom: 14 }}>
          <h1 style={{ fontSize: 19, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.02em", margin: 0, lineHeight: 1.25 }}>
            Trends
          </h1>
          <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "3px 0 0", lineHeight: 1.5 }}>
            How automation exposure metrics shift across dataset versions over time.
          </p>
        </div>
        <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden", width: "fit-content" }}>
          {([
            { value: "occupation",      label: "Occupation Categories" },
            { value: "work-activities", label: "Work Activities"       },
          ] as const).map(({ value, label }, i) => (
            <button
              key={value} onClick={() => setActiveTab(value)}
              style={{
                padding: "6px 16px", fontSize: 12,
                fontWeight: activeTab === value ? 700 : 500,
                background: activeTab === value ? "var(--brand-light)" : "transparent",
                color: activeTab === value ? "var(--brand)" : "var(--text-secondary)",
                border: "none", borderRight: i === 0 ? "1px solid var(--border)" : "none",
                cursor: "pointer", transition: "background 0.12s",
              }}
            >{label}</button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 24px 32px" }}>
        {activeTab === "occupation"
          ? <OccupationTrends config={config} />
          : <WorkActivityTrends config={config} />
        }
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
