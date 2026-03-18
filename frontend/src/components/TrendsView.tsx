"use client";

import { useState, useCallback, useRef, useMemo } from "react";
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
  metric: MetricKey,
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
  options, value, onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
      {options.map(({ value: v, label }, i) => (
        <button
          key={v} onClick={() => onChange(v)}
          style={{
            padding: "5px 11px", fontSize: 12,
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

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
      <div onClick={() => onChange(!checked)} style={{
        width: 30, height: 17, borderRadius: 9, cursor: "pointer",
        background: checked ? "var(--brand)" : "var(--border)",
        position: "relative", transition: "background 0.15s", flexShrink: 0,
      }}>
        <div style={{
          position: "absolute", top: 2, left: checked ? 15 : 2,
          width: 13, height: 13, borderRadius: "50%", background: "#fff",
          transition: "left 0.15s", boxShadow: "0 1px 2px rgba(0,0,0,0.15)",
        }} />
      </div>
      <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{label}</span>
    </label>
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
  loading, error, hasResult, lockedLine, setLockedLine,
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
}) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [hoveredLine, setHoveredLine] = useState<string | null>(null);

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
  function TrendsTooltip(props: any) {
    if (!props.active || !props.payload?.length) return null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const payload = activeLine ? props.payload.filter((p: any) => p.dataKey === activeLine) : props.payload;
    return (
      <div style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 8, padding: "10px 14px", fontSize: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.09)", maxWidth: 360,
      }}>
        <p style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
          {fmtDate(props.label ?? "")}
        </p>
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {payload.map((p: any, i: number) => {
          const inc = increases?.get(p.name);
          return (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 3, alignItems: "baseline" }}>
              <span style={{ color: p.color, fontWeight: 500, fontSize: 11, flex: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.name}</span>
              <span style={{ color: "var(--text-primary)", fontWeight: 600, whiteSpace: "nowrap" }}>
                {fmtVal(p.value ?? 0, metric)}
              </span>
              {inc != null && (
                <span style={{ fontSize: 10, fontWeight: 600, whiteSpace: "nowrap", color: inc >= 0 ? "#16a34a" : "#dc2626" }}>
                  {fmtIncrease(inc, metric, incMode)}
                </span>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div
      style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 12, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
      }}
      onClick={(e) => {
        // Click on chart background clears lock
        if ((e.target as HTMLElement).closest(".recharts-line")) return;
        if ((e.target as HTMLElement).closest("[data-legend-btn]")) return;
        setLockedLine(null);
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
              margin={{ top: 10, right: 30, bottom: 20, left: 60 }}
              onMouseLeave={() => { if (!lockedLine) setHoveredLine(null); }}
            >
              <CartesianGrid strokeDasharray="4 4" stroke="rgba(0,0,0,0.05)" vertical={false} />
              <XAxis
                dataKey="date" tickFormatter={fmtDate}
                tick={{ fontSize: 11, fill: "#888", fontFamily: CHART_FONT }}
                axisLine={{ stroke: "rgba(0,0,0,0.08)" }} tickLine={false}
              />
              <YAxis
                tickFormatter={(v: number) => fmtVal(v, metric)}
                tick={{ fontSize: 11, fill: "#888", fontFamily: CHART_FONT }}
                axisLine={false} tickLine={false} width={56}
              />
              <Tooltip content={(p) => <TrendsTooltip {...p} />} />
              {lineConfigs.map((lc) => {
                const isActive = activeLine === lc.key;
                const isDimmed = activeLine != null && !isActive;
                return (
                  <Line
                    key={lc.key} type="monotone" dataKey={lc.key} stroke={lc.color}
                    strokeWidth={isDimmed ? 1.5 : isActive ? 3.5 : 2.5}
                    opacity={isDimmed ? 0.25 : 1}
                    dot={{ r: 4.5, strokeWidth: 0, fill: lc.color }}
                    activeDot={{
                      r: 7, strokeWidth: 2, stroke: "#fff",
                      onClick: () => setLockedLine(lockedLine === lc.key ? null : lc.key),
                    }}
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <ControlLabel>Datasets</ControlLabel>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={onAll}  style={{ fontSize: 10, color: "var(--brand)",      background: "none", border: "none", cursor: "pointer", padding: 0 }}>All</button>
          <button onClick={onNone} style={{ fontSize: 10, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>None</button>
        </div>
      </div>
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
        {allDatasets.map((ds) => (
          <DatasetPill key={ds} label={ds} active={selectedDatasets.includes(ds)} onClick={() => onToggle(ds)} />
        ))}
      </div>
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

  // Sort / increase options
  const [sortMode,     setSortMode]     = useState<SortMode>("value");
  const [incMode,      setIncMode]      = useState<IncMode>("abs");

  // Search / context
  const [trendSearch,  setTrendSearch]  = useState("");
  const [ctxSize,      setCtxSize]      = useState(5);
  const searchFocused = useRef(false);

  // Lock state shared across the single chart panel
  const [lockedLine, setLockedLine] = useState<string | null>(null);

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
      setResult(data);
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

  // Apply sort-by-increase: sort full pool, then slice to topN
  const sortedCats = useMemo(() => {
    if (sortMode !== "increase" || !allIncreases) return allCats.slice(0, topN);
    const getInc = (cat: string) => {
      // For individual mode the keys are "ds — cat"; aggregate mode keys are just the cat name
      let max = -Infinity;
      allIncreases.forEach((v, key) => {
        if (key === cat || key.endsWith(` — ${cat}`)) max = Math.max(max, v);
      });
      return max === -Infinity ? -Infinity : max;
    };
    return [...allCats].sort((a, b) => getInc(b) - getInc(a)).slice(0, topN);
  }, [allCats, topN, sortMode, allIncreases]);

  // Apply search filter
  const shownCats = useMemo(() => {
    const q = trendSearch.trim().toLowerCase();
    if (!q) return sortedCats;
    const idx = sortedCats.findIndex((c) => c.toLowerCase().includes(q));
    if (idx < 0) return [];
    const start = Math.max(0, idx - ctxSize);
    const end   = Math.min(sortedCats.length, idx + ctxSize + 1);
    return sortedCats.slice(start, end);
  }, [sortedCats, trendSearch, ctxSize]);

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

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

        <DatasetSelector
          allDatasets={allDatasets} selectedDatasets={selectedDatasets}
          onToggle={(ds) => setSelectedDatasets((p) => p.includes(ds) ? p.filter((x) => x !== ds) : [...p, ds])}
          onAll={() => setSelectedDatasets(allDatasets)}
          onNone={() => setSelectedDatasets([])}
        />

        {/* Row 2 */}
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
          <div>
            <ControlLabel>Top {topN}</ControlLabel>
            <input type="range" min={2} max={20} value={topN} onChange={(e) => setTopN(Number(e.target.value))}
              style={{ width: 96, accentColor: "var(--brand)", display: "block" }} />
          </div>
          <button onClick={run} className="btn-brand" style={{ padding: "9px 24px", fontSize: 13 }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}>
            Run
          </button>
        </div>

        {/* Row 3 */}
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
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
          <div style={{ display: "flex", gap: 16, alignItems: "center", paddingBottom: 2 }}>
            <Toggle label="Auto-aug" checked={useAutoAug} onChange={setUseAutoAug} />
            {useAutoAug && hasMCP && (
              <Toggle label="Adj mean (MCP)" checked={useAdjMean} onChange={setUseAdjMean} />
            )}
          </div>
        </div>

        {/* Row 4 — Sort + Search (only shown when result is loaded) */}
        {result && (
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
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
            {sortMode === "increase" && (
              <div>
                <ControlLabel>Increase type</ControlLabel>
                <SegmentedControl
                  options={[{ value: "abs" as IncMode, label: "Absolute" }, { value: "pct" as IncMode, label: "% change" }]}
                  value={incMode} onChange={setIncMode}
                />
              </div>
            )}
            {/* Search */}
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
        )}
      </div>

      <div style={{ marginTop: 24 }}>
        <ChartPanel
          title={`${metaLabel} over time`} metric={metric}
          chartData={chartData} lineConfigs={lineConfigs}
          increases={sortMode === "increase" ? increases : null}
          incMode={incMode}
          loading={loading} error={error} hasResult={!!result}
          lockedLine={lockedLine} setLockedLine={setLockedLine}
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

  const [sortMode,  setSortMode]  = useState<SortMode>("value");
  const [incMode,   setIncMode]   = useState<IncMode>("abs");
  const [trendSearch, setTrendSearch] = useState("");
  const [ctxSize,   setCtxSize]   = useState(5);
  const [lockedLine, setLockedLine] = useState<string | null>(null);

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
      setResult(data);
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

  const sortedCats = useMemo(() => {
    if (sortMode !== "increase" || !allIncreases) return allCats.slice(0, topN);
    const getInc = (cat: string) => {
      let max = -Infinity;
      allIncreases.forEach((v, key) => {
        if (key === cat || key.endsWith(` — ${cat}`)) max = Math.max(max, v);
      });
      return max === -Infinity ? -Infinity : max;
    };
    return [...allCats].sort((a, b) => getInc(b) - getInc(a)).slice(0, topN);
  }, [allCats, topN, sortMode, allIncreases]);

  const shownCats = useMemo(() => {
    const q = trendSearch.trim().toLowerCase();
    if (!q) return sortedCats;
    const idx = sortedCats.findIndex((c) => c.toLowerCase().includes(q));
    if (idx < 0) return [];
    const start = Math.max(0, idx - ctxSize);
    const end   = Math.min(sortedCats.length, idx + ctxSize + 1);
    return sortedCats.slice(start, end);
  }, [sortedCats, trendSearch, ctxSize]);

  const { chartData, lineConfigs } = result
    ? lineMode === "individual"
      ? buildIndividualData(result, selectedDatasets, shownCats, metric)
      : buildAggregatedData(result, selectedDatasets, shownCats, metric, lineMode)
    : { chartData: [], lineConfigs: [] };

  const increases = useMemo(
    () => lineConfigs.length > 0 ? computeIncreases(chartData, lineConfigs, metric, incMode) : null,
    [chartData, lineConfigs, metric, incMode],
  );

  const levelLabels: Record<string, string> = {
    gwa: "General Work Activities", iwa: "Intermediate Work Activities", dwa: "Detailed Work Activities",
  };

  return (
    <>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

        <DatasetSelector
          allDatasets={allDatasets} selectedDatasets={selectedDatasets}
          onToggle={(ds) => setSelectedDatasets((p) => p.includes(ds) ? p.filter((x) => x !== ds) : [...p, ds])}
          onAll={() => setSelectedDatasets(allDatasets)}
          onNone={() => setSelectedDatasets([])}
        />

        {/* Row 2 */}
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
          <div>
            <ControlLabel>Top {topN}</ControlLabel>
            <input type="range" min={2} max={20} value={topN} onChange={(e) => setTopN(Number(e.target.value))}
              style={{ width: 96, accentColor: "var(--brand)", display: "block" }} />
          </div>
          <button onClick={run} className="btn-brand" style={{ padding: "9px 24px", fontSize: 13 }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}>
            Run
          </button>
        </div>

        {/* Row 3 */}
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
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
          <div style={{ display: "flex", gap: 16, alignItems: "center", paddingBottom: 2 }}>
            <Toggle label="Auto-aug" checked={useAutoAug} onChange={setUseAutoAug} />
            {useAutoAug && hasMCP && (
              <Toggle label="Adj mean (MCP)" checked={useAdjMean} onChange={setUseAdjMean} />
            )}
          </div>
        </div>

        {/* Row 4 — Sort + Search */}
        {result && (
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
            <div>
              <ControlLabel>Sort</ControlLabel>
              <SegmentedControl
                options={[{ value: "value" as SortMode, label: "By value" }, { value: "increase" as SortMode, label: "By increase" }]}
                value={sortMode} onChange={setSortMode}
              />
            </div>
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
        )}
      </div>

      <p style={{ fontSize: 11, color: "var(--text-muted)", margin: "8px 0 0" }}>
        AEI series uses ECO 2015 baseline · MCP/Microsoft uses ECO 2025 — lines are not directly comparable
      </p>

      <div style={{ marginTop: 16 }}>
        <ChartPanel
          title={`${levelLabels[activityLevel]} — ${metaLabel} over time`} metric={metric}
          chartData={chartData} lineConfigs={lineConfigs}
          increases={sortMode === "increase" ? increases : null}
          incMode={incMode}
          loading={loading} error={error} hasResult={!!result}
          lockedLine={lockedLine} setLockedLine={setLockedLine}
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
