"use client";

import { useState, useCallback, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { ConfigResponse, TrendsSettings, TrendsResponse, TrendSeries } from "@/lib/types";
import { fetchTrends } from "@/lib/api";
import { downloadChartAsPng } from "@/lib/downloadChart";

interface Props {
  config: ConfigResponse;
}

// ── Colors ────────────────────────────────────────────────────────────────────

const SERIES_COLORS: Record<string, string[]> = {
  AEI:       ["#3a5f83", "#5a7f9e", "#7a9eb8", "#9abdd2"],
  "AEI API": ["#2d4a6b", "#4d6a8b"],
  MCP:       ["#4a7c6f", "#6a9c8f", "#7ab09e", "#8ac3b0"],
  Microsoft: ["#c05621"],
};

function getColor(seriesName: string, idx: number): string {
  const palette = SERIES_COLORS[seriesName] ?? ["#888"];
  return palette[idx % palette.length];
}

// ── Formatters ────────────────────────────────────────────────────────────────

type MetricKey = "workers_affected" | "wages_affected" | "pct_tasks_affected";

const METRIC_OPTIONS: { key: MetricKey; label: string }[] = [
  { key: "workers_affected",   label: "Workers Affected" },
  { key: "wages_affected",     label: "Wages Affected ($B)" },
  { key: "pct_tasks_affected", label: "% Tasks Affected" },
];

const AGG_OPTIONS = [
  { value: "major",      label: "Major" },
  { value: "minor",      label: "Minor" },
  { value: "broad",      label: "Broad" },
  { value: "occupation", label: "Occupation" },
];

function fmtVal(v: number, metric: MetricKey): string {
  if (metric === "workers_affected")   return v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : `${(v / 1e3).toFixed(0)}K`;
  if (metric === "wages_affected")     return `$${v.toFixed(2)}B`;
  if (metric === "pct_tasks_affected") return `${v.toFixed(1)}%`;
  return String(v);
}

function fmtDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00Z");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[d.getUTCMonth()]} '${String(d.getUTCFullYear()).slice(2)}`;
}

const CHART_FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif";

// ── Data transformation ───────────────────────────────────────────────────────

function buildRechartsData(
  result: TrendsResponse,
  shownCats: string[],
  metric: MetricKey,
) {
  const dateSet = new Set<string>();
  result.series.forEach((s: TrendSeries) =>
    s.data_points.forEach((dp) => dateSet.add(dp.date)),
  );
  const dates = Array.from(dateSet).sort();

  // (date, lineKey) → value
  const valueMap = new Map<string, number>();
  result.series.forEach((series: TrendSeries) => {
    shownCats.forEach((cat) => {
      const lineKey = `${series.name} — ${cat}`;
      series.data_points.forEach((dp) => {
        const row = dp.rows.find((r) => r.category === cat);
        if (row) {
          const raw = row[metric] as number;
          const v   = metric === "wages_affected" ? raw / 1e9 : raw;
          valueMap.set(`${dp.date}::${lineKey}`, v);
        }
      });
    });
  });

  const chartData = dates.map((date) => {
    const point: Record<string, number | string> = { date };
    result.series.forEach((series: TrendSeries) => {
      shownCats.forEach((cat) => {
        const key = `${series.name} — ${cat}`;
        const v   = valueMap.get(`${date}::${key}`);
        if (v !== undefined) point[key] = v;
      });
    });
    return point;
  });

  const lineConfigs = result.series
    .flatMap((series: TrendSeries) =>
      shownCats.map((cat, catIdx) => ({
        key:   `${series.name} — ${cat}`,
        color: getColor(series.name, catIdx),
      })),
    )
    .filter((lc) => dates.some((d) => valueMap.has(`${d}::${lc.key}`)));

  return { chartData, lineConfigs };
}

// ── Controls ──────────────────────────────────────────────────────────────────

function ControlLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontSize: 10, fontWeight: 700,
      color: "var(--text-muted)",
      textTransform: "uppercase",
      letterSpacing: "0.08em",
      marginBottom: 6,
    }}>
      {children}
    </p>
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
    <div style={{
      display: "flex",
      border: "1px solid var(--border)",
      borderRadius: 7,
      overflow: "hidden",
    }}>
      {options.map(({ value: v, label }, i) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          style={{
            padding: "5px 11px",
            fontSize: 12, fontWeight: value === v ? 600 : 400,
            background: value === v ? "var(--brand-light)" : "transparent",
            color: value === v ? "var(--brand)" : "var(--text-secondary)",
            border: "none",
            borderRight: i < options.length - 1 ? "1px solid var(--border)" : "none",
            cursor: "pointer",
            transition: "background 0.12s",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function SeriesToggle({
  label, active, onClick,
}: {
  label: string; active: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        fontSize: 12, padding: "5px 11px",
        borderRadius: 6,
        border: `1.5px solid ${active ? "var(--brand)" : "var(--border)"}`,
        background: active ? "var(--brand-light)" : "transparent",
        color: active ? "var(--brand)" : "var(--text-secondary)",
        cursor: "pointer", fontWeight: active ? 600 : 400,
        transition: "all 0.12s",
      }}
    >
      {label}
    </button>
  );
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

// ── Main component ────────────────────────────────────────────────────────────

export default function TrendsView({ config }: Props) {
  const allSeries = Object.keys(config.dataset_series ?? {});

  const [selectedSeries, setSelectedSeries] = useState<string[]>(["AEI", "MCP"]);
  const [metric,   setMetric]   = useState<MetricKey>("workers_affected");
  const [aggLevel, setAggLevel] = useState("major");
  const [method,   setMethod]   = useState<"freq" | "imp">("freq");
  const [geo,      setGeo]      = useState<"nat" | "ut">("nat");
  const [topN,     setTopN]     = useState(8);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [result,   setResult]   = useState<TrendsResponse | null>(null);
  const [shownCats, setShownCats] = useState<string[]>([]);

  const chartRef = useRef<HTMLDivElement>(null);

  const run = useCallback(async () => {
    if (!selectedSeries.length) return;
    setLoading(true); setError(null);
    try {
      const settings: TrendsSettings = {
        series: selectedSeries, method, useAutoAug: false, useAdjMean: false,
        physicalMode: "all", geo, aggLevel: aggLevel as TrendsSettings["aggLevel"],
        topN, sortBy: "Workers Affected",
      };
      const data = await fetchTrends(settings);
      setResult(data);
      const cats = new Set<string>();
      data.series.forEach((s: TrendSeries) => s.top_categories.forEach((c) => cats.add(c)));
      setShownCats(Array.from(cats).slice(0, topN));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch trends");
    } finally {
      setLoading(false);
    }
  }, [selectedSeries, metric, aggLevel, method, geo, topN]);

  const metaLabel = METRIC_OPTIONS.find((m) => m.key === metric)?.label ?? "";

  const { chartData, lineConfigs } = result
    ? buildRechartsData(result, shownCats, metric)
    : { chartData: [], lineConfigs: [] };

  const chartHeight = Math.max(420, Math.min(shownCats.length, 12) * 40 + 180);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function TrendsTooltip(props: any) {
    if (!props.active || !props.payload?.length) return null;
    return (
      <div style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "10px 14px",
        fontSize: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.09)",
        maxWidth: 300,
      }}>
        <p style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
          {fmtDate(props.label ?? "")}
        </p>
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
        {props.payload.map((p: any, i: number) => (
          <div key={i} style={{
            display: "flex", justifyContent: "space-between",
            gap: 16, marginBottom: 3, alignItems: "baseline",
          }}>
            <span style={{ color: p.color, fontWeight: 500, fontSize: 11, flex: 1 }}>
              {p.name}
            </span>
            <span style={{ color: "var(--text-primary)", fontWeight: 600, whiteSpace: "nowrap" }}>
              {fmtVal(p.value ?? 0, metric)}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "calc(100vh - var(--nav-height))",
      overflow: "hidden",
    }}>
      {/* ── Top bar ── */}
      <div style={{
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        padding: "0 24px",
        height: 52,
        display: "flex", alignItems: "center",
        flexShrink: 0,
      }}>
        <div>
          <h1 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.01em", margin: 0 }}>
            Trends
          </h1>
          <p style={{ fontSize: 11, color: "var(--text-muted)", margin: 0 }}>
            How automation exposure metrics shift across dataset versions over time.
          </p>
        </div>
      </div>

      {/* ── Controls bar ── */}
      <div style={{
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        padding: "14px 24px",
        flexShrink: 0,
      }}>
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "flex-end" }}>

          {/* Dataset series — multi-select pills */}
          <div>
            <ControlLabel>Dataset series</ControlLabel>
            <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
              {allSeries.map((s) => (
                <SeriesToggle
                  key={s} label={s} active={selectedSeries.includes(s)}
                  onClick={() =>
                    setSelectedSeries((prev) =>
                      prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
                    )
                  }
                />
              ))}
            </div>
          </div>

          {/* Metric — segmented */}
          <div>
            <ControlLabel>Metric</ControlLabel>
            <SegmentedControl
              options={METRIC_OPTIONS.map((m) => ({ value: m.key, label: m.label }))}
              value={metric}
              onChange={setMetric}
            />
          </div>

          {/* Aggregation — segmented */}
          <div>
            <ControlLabel>Aggregation</ControlLabel>
            <SegmentedControl
              options={AGG_OPTIONS.map((a) => ({ value: a.value, label: a.label }))}
              value={aggLevel}
              onChange={setAggLevel}
            />
          </div>

          {/* Method — segmented */}
          <div>
            <ControlLabel>Method</ControlLabel>
            <SegmentedControl
              options={[
                { value: "freq", label: "Frequency" },
                { value: "imp",  label: "Importance" },
              ]}
              value={method}
              onChange={setMethod}
            />
          </div>

          {/* Geography — segmented */}
          <div>
            <ControlLabel>Geography</ControlLabel>
            <SegmentedControl
              options={[
                { value: "nat", label: "National" },
                { value: "ut",  label: "Utah" },
              ]}
              value={geo}
              onChange={setGeo}
            />
          </div>

          {/* Top N slider */}
          <div>
            <ControlLabel>Top {topN} categories</ControlLabel>
            <input
              type="range" min={2} max={20} value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              style={{ width: 96, accentColor: "var(--brand)", display: "block" }}
            />
          </div>

          {/* Run */}
          <button
            onClick={run}
            className="btn-brand"
            style={{ padding: "9px 24px", fontSize: 13 }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}
          >
            Run
          </button>
        </div>
      </div>

      {/* ── Chart area ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {loading && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
            <span style={{ marginLeft: 10, fontSize: 13, color: "var(--text-muted)" }}>
              Computing trends…
            </span>
          </div>
        )}

        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#b91c1c" }}>
            Error: {error}
          </div>
        )}

        {!loading && !error && !result && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: 300, background: "var(--bg-surface)",
            border: "1px solid var(--border)", borderRadius: 12,
          }}>
            <div style={{ textAlign: "center" }}>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500, marginBottom: 4 }}>
                Select series and click Run to view trends
              </p>
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Tracks how {metaLabel || "metrics"} changed across dataset versions
              </p>
            </div>
          </div>
        )}

        {!loading && !error && result && lineConfigs.length > 0 && (
          <div style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            overflow: "hidden",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          }}>
            {/* Chart card header */}
            <div style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "14px 20px 8px",
            }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                {metaLabel} over time
              </span>
              <button
                onClick={() => downloadChartAsPng(chartRef.current, `trends-${metric}`)}
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

            <div ref={chartRef} style={{ padding: "0 16px 16px" }}>
              <ResponsiveContainer width="100%" height={chartHeight}>
                <LineChart
                  data={chartData}
                  margin={{ top: 10, right: 30, bottom: 20, left: 60 }}
                >
                  <CartesianGrid
                    strokeDasharray="4 4"
                    stroke="rgba(0,0,0,0.05)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    tickFormatter={fmtDate}
                    tick={{ fontSize: 11, fill: "#888", fontFamily: CHART_FONT }}
                    axisLine={{ stroke: "rgba(0,0,0,0.08)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tickFormatter={(v: number) => fmtVal(v, metric)}
                    tick={{ fontSize: 11, fill: "#888", fontFamily: CHART_FONT }}
                    axisLine={false}
                    tickLine={false}
                    width={56}
                  />
                  <Tooltip content={(p) => <TrendsTooltip {...p} />} />
                  <Legend
                    wrapperStyle={{
                      fontSize: 11,
                      fontFamily: CHART_FONT,
                      paddingTop: 12,
                      color: "var(--text-secondary)",
                    }}
                  />
                  {lineConfigs.map((lc) => (
                    <Line
                      key={lc.key}
                      type="monotone"
                      dataKey={lc.key}
                      stroke={lc.color}
                      strokeWidth={2}
                      dot={{ r: 4, strokeWidth: 0, fill: lc.color }}
                      activeDot={{ r: 5 }}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {!loading && !error && result && lineConfigs.length === 0 && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: 200, background: "var(--bg-surface)",
            border: "1px solid var(--border)", borderRadius: 12,
            fontSize: 13, color: "var(--text-muted)",
          }}>
            No matching data found for the selected configuration.
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
