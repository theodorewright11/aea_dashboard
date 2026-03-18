"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import type { GroupSettings, ChartRow, ConfigResponse } from "@/lib/types";
import { fetchCompute } from "@/lib/api";
import HorizontalBarChart from "./HorizontalBarChart";
import { downloadChartAsPng } from "@/lib/downloadChart";

interface Props {
  groupId: "A" | "B";
  color: string;
  settings: GroupSettings;
  config: ConfigResponse;
}

const METRIC_TITLES = {
  workers: "Workers Affected",
  wages:   "Wages Affected",
  tasks:   "% Tasks Affected",
} as const;

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

// ── Chart card with header + download ────────────────────────────────────────

function ChartCard({
  title, downloadSlug, children,
}: {
  title: string;
  downloadSlug: string;
  children: React.ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderRadius: 10,
      overflow: "hidden",
      boxShadow: "0 1px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
    }}>
      {/* Card header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "12px 16px 4px",
      }}>
        <span style={{
          fontSize: 13, fontWeight: 600,
          color: "var(--text-primary)",
          letterSpacing: "-0.01em",
        }}>
          {title}
        </span>
        <button
          onClick={() => downloadChartAsPng(containerRef.current, downloadSlug)}
          title={`Download ${title} as PNG`}
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

      {/* Chart area — containerRef wraps just the chart SVG */}
      <div ref={containerRef} style={{ padding: "0 8px 12px" }}>
        {children}
      </div>
    </div>
  );
}

// ── GroupPanel ────────────────────────────────────────────────────────────────

export default function GroupPanel({ groupId, color, settings, config }: Props) {
  const [rows, setRows]       = useState<ChartRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!settings.selectedDatasets.length) { setRows([]); return; }
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchCompute(settings);
      setRows(resp.rows);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load data");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [settings]);

  useEffect(() => { load(); }, [load]);

  // Build a human-readable slug for the download filename
  const ds     = settings.selectedDatasets.join("+") || "none";
  const method = settings.method === "freq" ? "freq" : "imp";
  const geo    = settings.geo;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, width: "100%", minWidth: 0 }}>
      {/* Group header badge */}
      <div style={{
        backgroundColor: color,
        borderRadius: 8,
        padding: "10px 16px",
        color: "white",
        fontSize: 14, fontWeight: 700,
        letterSpacing: "-0.01em",
      }}>
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

      {!loading && !error && (
        <>
          {(["workers", "wages", "tasks"] as const).map((metric) => (
            <ChartCard
              key={metric}
              title={METRIC_TITLES[metric]}
              downloadSlug={`group-${groupId}-${metric}-${ds}-${method}-${geo}`}
            >
              <HorizontalBarChart
                rows={rows ?? []}
                metric={metric}
                color={color}
              />
            </ChartCard>
          ))}
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
