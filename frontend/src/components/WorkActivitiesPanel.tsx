"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import type { GroupSettings, WorkActivitiesResponse, ActivityGroup, ActivityRow } from "@/lib/types";
import { fetchWorkActivities } from "@/lib/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type ActivityLevel = "gwa" | "iwa" | "dwa";

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

function fmt(v: number, type: "number" | "billion" | "percent"): string {
  if (type === "number")  return v.toLocaleString("en-US", { maximumFractionDigits: 0 });
  if (type === "billion") return `$${(v / 1e9).toFixed(2)}B`;
  return `${v.toFixed(1)}%`;
}

function ActivityChart({ rows, color, metric }: { rows: ActivityRow[]; color: string; metric: "workers" | "wages" | "tasks" }) {
  if (!rows.length) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 120, background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--text-muted)" }}>
      No data
    </div>
  );

  const metaMap = {
    workers: { col: "workers_affected" as keyof ActivityRow, title: "Workers Affected", label: "Workers", type: "number" as const },
    wages:   { col: "wages_affected"   as keyof ActivityRow, title: "Wages Affected",   label: "$B",      type: "billion" as const },
    tasks:   { col: "pct_tasks_affected" as keyof ActivityRow, title: "% Tasks Affected", label: "%",     type: "percent" as const },
  };
  const meta = metaMap[metric];

  const rawVals  = rows.map((r) => r[meta.col] as number);
  const total    = rawVals.reduce((a, b) => a + b, 0);
  const plotVals = metric === "wages" ? rawVals.map((v) => v / 1e9) : rawVals;
  const cats     = rows.map((r) => r.category);

  const labels = rawVals.map((v) => {
    if (metric === "tasks") return `${v.toFixed(1)}%`;
    const share = total > 0 ? (v / total) * 100 : 0;
    return `${fmt(v, meta.type)} (${share.toFixed(1)}%)`;
  });

  const n = rows.length;
  const height = Math.max(240, 32 * n + 100);

  return (
    <Plot
      data={[{
        type: "bar", orientation: "h",
        x: plotVals, y: cats,
        marker: { color, line: { width: 0 } },
        text: labels,
        textposition: "inside", insidetextanchor: "middle",
        textfont: { color: "white", size: 10 },
        hoverinfo: "text",
        hovertext: cats.map((cat, i) => `<b>${cat}</b><br>${fmt(rawVals[i], meta.type)}`),
        cliponaxis: false,
      }]}
      layout={{
        title: { text: `<b>${meta.title}</b>`, font: { size: 13, color: "#1a1a1a" }, x: 0, xanchor: "left" },
        xaxis: { tickfont: { size: 9, color: "#666" }, showgrid: true, gridcolor: "rgba(200,200,200,0.3)" },
        yaxis: { tickfont: { size: 9, color: "#333" }, automargin: true },
        height, margin: { l: 8, r: 20, t: 36, b: 24 },
        plot_bgcolor: "white", paper_bgcolor: "white", showlegend: false, bargap: 0.3,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
      useResizeHandler
    />
  );
}

function ActivityGroupPanel({ group, color, label }: { group: ActivityGroup; color: string; label: string }) {
  const [level, setLevel] = useState<ActivityLevel>("gwa");
  const [metric, setMetric] = useState<"workers" | "wages" | "tasks">("workers");

  const rows = group[level] ?? [];

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
      {/* Sub-panel header */}
      <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border-light)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>{label}</span>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {(["gwa", "iwa", "dwa"] as ActivityLevel[]).map((l) => (
            <button key={l} onClick={() => setLevel(l)}
              style={{ fontSize: 11, padding: "3px 10px", borderRadius: 5, border: `1px solid ${l === level ? color : "var(--border)"}`, background: l === level ? color : "transparent", color: l === level ? "white" : "var(--text-secondary)", cursor: "pointer", fontWeight: l === level ? 600 : 400 }}>
              {l.toUpperCase()}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {(["workers", "wages", "tasks"] as const).map((m) => (
            <button key={m} onClick={() => setMetric(m)}
              style={{ fontSize: 11, padding: "3px 10px", borderRadius: 5, border: `1px solid ${m === metric ? "var(--brand)" : "var(--border)"}`, background: m === metric ? "var(--brand-light)" : "transparent", color: m === metric ? "var(--brand)" : "var(--text-secondary)", cursor: "pointer", fontWeight: m === metric ? 600 : 400 }}>
              {m === "workers" ? "Workers" : m === "wages" ? "Wages" : "% Tasks"}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: "0 8px 8px" }}>
        <div style={{ fontSize: 10, color: "var(--text-muted)", padding: "6px 6px 0" }}>{LEVEL_LABELS[level]}</div>
        <ActivityChart rows={rows} color={color} metric={metric} />
      </div>
    </div>
  );
}

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
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Group header */}
      <div style={{ backgroundColor: color, borderRadius: 8, padding: "10px 16px", color: "white", fontSize: 14, fontWeight: 700 }}>
        Group {groupId}
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
        <ActivityGroupPanel group={data.aei_group} color={color}
          label={`AEI Group — ${data.aei_group.datasets.join(", ")} (ECO 2015 baseline)`} />
      )}
      {!loading && !error && data?.mcp_group && (
        <ActivityGroupPanel group={data.mcp_group} color={color}
          label={`MCP / Microsoft Group — ${data.mcp_group.datasets.join(", ")} (ECO 2025 baseline)`} />
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
