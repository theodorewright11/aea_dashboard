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
  title, downloadSlug, accentColor, children,
}: {
  title: string;
  downloadSlug: string;
  accentColor: string;
  children: React.ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderLeft: `3px solid ${accentColor}`,
      borderRadius: 12,
      overflow: "hidden",
      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
    }}>
      {/* Card header */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 18px 4px",
      }}>
        <span style={{
          fontSize: 14, fontWeight: 600,
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
      <div ref={containerRef} style={{ padding: "0 12px 16px" }}>
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

      {!loading && !error && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {(["workers", "wages", "tasks"] as const).map((metric) => (
            <ChartCard
              key={metric}
              title={METRIC_TITLES[metric]}
              downloadSlug={`group-${groupId}-${metric}-${ds}-${method}-${geo}`}
              accentColor={color}
            >
              <HorizontalBarChart
                rows={rows ?? []}
                metric={metric}
                color={color}
              />
            </ChartCard>
          ))}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
