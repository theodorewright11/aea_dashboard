"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import type { ConfigResponse, TrendsSettings, TrendsResponse, TrendSeries } from "@/lib/types";
import { fetchTrends } from "@/lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface Props {
  config: ConfigResponse;
}

// Fixed colors per series
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

type MetricKey = "workers_affected" | "wages_affected" | "pct_tasks_affected";

const METRIC_OPTIONS: { key: MetricKey; label: string }[] = [
  { key: "workers_affected",   label: "Workers Affected" },
  { key: "wages_affected",     label: "Wages Affected ($B)" },
  { key: "pct_tasks_affected", label: "% Tasks Affected" },
];

function fmtVal(v: number, metric: MetricKey): string {
  if (metric === "workers_affected")   return v.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (metric === "wages_affected")     return `$${(v / 1e9).toFixed(2)}B`;
  if (metric === "pct_tasks_affected") return `${v.toFixed(1)}%`;
  return String(v);
}

const AGG_OPTIONS = [
  { value: "major",      label: "Major Category" },
  { value: "minor",      label: "Minor Category" },
  { value: "broad",      label: "Broad Occupation" },
  { value: "occupation", label: "Occupation" },
];

function ToggleButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      style={{ fontSize: 12, padding: "5px 12px", borderRadius: 6, border: `1.5px solid ${active ? "var(--brand)" : "var(--border)"}`, background: active ? "var(--brand-light)" : "transparent", color: active ? "var(--brand)" : "var(--text-secondary)", cursor: "pointer", fontWeight: active ? 600 : 400, transition: "all 0.12s" }}>
      {children}
    </button>
  );
}

export default function TrendsView({ config }: Props) {
  const allSeries = Object.keys(config.dataset_series ?? {});

  const [selectedSeries, setSelectedSeries] = useState<string[]>(["AEI", "MCP"]);
  const [metric, setMetric]   = useState<MetricKey>("workers_affected");
  const [aggLevel, setAggLevel] = useState("major");
  const [method, setMethod]   = useState<"freq" | "imp">("freq");
  const [geo, setGeo]         = useState<"nat" | "ut">("nat");
  const [topN, setTopN]       = useState(8);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [result, setResult]   = useState<TrendsResponse | null>(null);

  // All categories found across series
  const [shownCats, setShownCats] = useState<string[]>([]);

  const run = useCallback(async () => {
    if (!selectedSeries.length) return;
    setLoading(true); setError(null);
    try {
      const settings: TrendsSettings = {
        series: selectedSeries, method, useAutoAug: false, useAdjMean: false,
        physicalMode: "all", geo, aggLevel: aggLevel as TrendsSettings["aggLevel"], topN, sortBy: "Workers Affected",
      };
      const data = await fetchTrends(settings);
      setResult(data);
      // Collect top categories from all series
      const cats = new Set<string>();
      data.series.forEach((s) => s.top_categories.forEach((c) => cats.add(c)));
      setShownCats(Array.from(cats).slice(0, topN));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to fetch trends");
    } finally {
      setLoading(false);
    }
  }, [selectedSeries, metric, aggLevel, method, geo, topN]);

  // Build Plotly traces from result
  function buildTraces() {
    if (!result) return [];
    const traces: object[] = [];

    result.series.forEach((series: TrendSeries) => {
      // For each category, build one line per series
      shownCats.forEach((cat, catIdx) => {
        const dates: string[] = [];
        const vals:  number[] = [];

        series.data_points.forEach((dp) => {
          const row = dp.rows.find((r) => r.category === cat);
          if (row) {
            dates.push(dp.date);
            const raw = row[metric] as number;
            const v = metric === "wages_affected" ? raw / 1e9 : raw;
            vals.push(v);
          }
        });

        if (!dates.length) return;

        traces.push({
          type:    "scatter",
          mode:    "lines+markers",
          name:    `${series.name} — ${cat}`,
          x:       dates,
          y:       vals,
          line:    { color: getColor(series.name, catIdx), width: 2.5 },
          marker:  { size: 7, color: getColor(series.name, catIdx) },
          hovertemplate: `<b>${cat}</b><br>${series.name}: %{y}<extra></extra>`,
        });
      });
    });
    return traces;
  }

  const metaLabel = METRIC_OPTIONS.find((m) => m.key === metric)?.label ?? "";
  const traces = buildTraces();
  const chartHeight = Math.max(420, 60 * Math.min(shownCats.length, 12) + 120);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 56px)", overflow: "hidden" }}>
      {/* Top bar */}
      <div style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "0 24px", height: 52, display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>Trends</h1>
          <p style={{ fontSize: 11, color: "var(--text-muted)" }}>How automation exposure metrics change across dataset versions over time.</p>
        </div>
      </div>

      {/* Controls */}
      <div style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "14px 24px", flexShrink: 0 }}>
        <div style={{ display: "flex", gap: 24, flexWrap: "wrap", alignItems: "flex-start" }}>
          {/* Series selector */}
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Dataset series</p>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {allSeries.map((s) => (
                <ToggleButton key={s} active={selectedSeries.includes(s)}
                  onClick={() => setSelectedSeries((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s])}>
                  {s}
                </ToggleButton>
              ))}
            </div>
          </div>

          {/* Metric */}
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Metric</p>
            <div style={{ display: "flex", gap: 6 }}>
              {METRIC_OPTIONS.map(({ key, label }) => (
                <ToggleButton key={key} active={metric === key} onClick={() => setMetric(key)}>{label}</ToggleButton>
              ))}
            </div>
          </div>

          {/* Aggregation */}
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Aggregation</p>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {AGG_OPTIONS.map(({ value, label }) => (
                <ToggleButton key={value} active={aggLevel === value} onClick={() => setAggLevel(value)}>{label}</ToggleButton>
              ))}
            </div>
          </div>

          {/* Method + Geo */}
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Method</p>
            <div style={{ display: "flex", gap: 6 }}>
              <ToggleButton active={method === "freq"} onClick={() => setMethod("freq")}>Frequency</ToggleButton>
              <ToggleButton active={method === "imp"}  onClick={() => setMethod("imp")}>Importance</ToggleButton>
            </div>
          </div>
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Geography</p>
            <div style={{ display: "flex", gap: 6 }}>
              <ToggleButton active={geo === "nat"} onClick={() => setGeo("nat")}>National</ToggleButton>
              <ToggleButton active={geo === "ut"}  onClick={() => setGeo("ut")}>Utah</ToggleButton>
            </div>
          </div>

          {/* Top N + Run */}
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em" }}>Top {topN}</p>
            <input type="range" min={2} max={20} value={topN} onChange={(e) => setTopN(Number(e.target.value))}
              style={{ width: 100, accentColor: "var(--brand)" }} />
          </div>

          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <button onClick={run}
              style={{ background: "var(--brand)", color: "white", border: "none", borderRadius: 8, padding: "9px 22px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}
              onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
              onMouseOut={(e) => (e.currentTarget.style.background = "var(--brand)")}>
              Run
            </button>
          </div>
        </div>
      </div>

      {/* Chart area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {loading && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
            <span style={{ marginLeft: 10, fontSize: 13, color: "var(--text-muted)" }}>Computing trends…</span>
          </div>
        )}

        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#b91c1c" }}>
            Error: {error}
          </div>
        )}

        {!loading && !error && !result && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 300, background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 12 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>📈</div>
              <p style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500 }}>Select series and click Run to view trends</p>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>Tracks how {metaLabel || "metrics"} changed across dataset versions</p>
            </div>
          </div>
        )}

        {!loading && !error && result && traces.length > 0 && (
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 8px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
            <Plot
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              data={traces as any}
              layout={{
                title: {
                  text: `<b>${metaLabel}</b> over time`,
                  font: { size: 15, color: "#1a1a1a" },
                  x: 0.02, xanchor: "left",
                },
                xaxis: { title: { text: "Dataset version date", font: { size: 12, color: "#666" } }, tickfont: { size: 11, color: "#666" }, showgrid: true, gridcolor: "rgba(200,200,200,0.3)" },
                yaxis: { title: { text: metaLabel, font: { size: 12, color: "#666" } }, tickfont: { size: 11, color: "#666" }, showgrid: true, gridcolor: "rgba(200,200,200,0.3)" },
                height: chartHeight,
                margin: { l: 70, r: 30, t: 60, b: 60 },
                plot_bgcolor: "white",
                paper_bgcolor: "white",
                legend: { font: { size: 10 }, orientation: "v", x: 1.02, y: 1 },
                hovermode: "closest",
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: "100%" }}
              useResizeHandler
            />
          </div>
        )}

        {!loading && !error && result && traces.length === 0 && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200, background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 12, fontSize: 13, color: "var(--text-muted)" }}>
            No matching data found for the selected configuration.
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
