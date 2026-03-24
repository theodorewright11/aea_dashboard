"use client";

import { useRef } from "react";
import type { ComputeResponse } from "@/lib/types";
import HorizontalBarChart from "./HorizontalBarChart";
import { downloadChartAsPng } from "@/lib/downloadChart";

interface Props {
  groupId:        "A" | "B";
  color:          string;
  /** This group's compute result */
  response:       ComputeResponse | null;
  /** Other group's compute result — for delta tooltips */
  otherResponse:  ComputeResponse | null;
  loading:        boolean;
  error:          string | null;
  /** Highlight this category if search matched */
  matchedCategory?: string | null;
  /** Config summary lines shown as footer in downloaded PNGs */
  configSummary?: string[];
  /** When true, shows "Simple mode" label instead of "Group X" */
  simpleMode?: boolean;
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
  title, downloadSlug, downloadTitle, accentColor, configLines, children,
}: {
  title: string;
  downloadSlug: string;
  downloadTitle: string;
  accentColor: string;
  configLines?: string[];
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
        >
          <DownloadIcon />
        </button>
      </div>

      <div ref={containerRef} style={{ padding: "0 12px 16px" }}>
        {children}
      </div>
    </div>
  );
}

// ── GroupPanel ────────────────────────────────────────────────────────────────

export default function GroupPanel({
  groupId,
  color,
  response,
  otherResponse,
  loading,
  error,
  matchedCategory,
  configSummary,
  simpleMode = false,
}: Props) {
  const rows      = response?.rows      ?? [];
  const otherRows = otherResponse?.rows ?? [];

  const totalCategories = response?.total_categories ?? 0;
  const totalEmp        = response?.total_emp        ?? 0;
  const totalWages      = response?.total_wages      ?? 0;

  const datasetLabel = ""; // caller can add to group label if desired

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, width: "100%", minWidth: 0 }}>
      {/* Group label */}
      {!simpleMode && (
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 3, height: 18, borderRadius: 2, background: color, flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "-0.01em" }}>
          Group {groupId}{datasetLabel}
        </span>
      </div>
      )}

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

      {!loading && !error && response && rows.length === 0 && (
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, padding: "32px", textAlign: "center", fontSize: 13, color: "var(--text-muted)" }}>
          {matchedCategory === undefined && response.matched_category === null
            ? "No match found for your search."
            : "No data available for the selected settings."}
        </div>
      )}

      {!loading && !error && rows.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {(["workers", "wages", "tasks"] as const).map((metric) => (
            <ChartCard
              key={metric}
              title={METRIC_TITLES[metric]}
              downloadSlug={`group-${groupId}-${metric}`}
              downloadTitle={`Group ${groupId} — ${METRIC_TITLES[metric]}`}
              accentColor={color}
              configLines={configSummary}
            >
              <HorizontalBarChart
                rows={rows}
                metric={metric}
                color={color}
                totalCategories={totalCategories}
                totalEmp={totalEmp}
                totalWages={totalWages}
                otherGroupRows={otherRows}
                matchedCategory={matchedCategory ?? response?.matched_category}
              />
            </ChartCard>
          ))}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
