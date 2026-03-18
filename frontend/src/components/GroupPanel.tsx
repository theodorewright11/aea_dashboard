"use client";

import { useEffect, useState, useCallback } from "react";
import type { GroupSettings, ChartRow, ConfigResponse } from "@/lib/types";
import { fetchCompute } from "@/lib/api";
import HorizontalBarChart from "./HorizontalBarChart";

interface Props {
  groupId: "A" | "B";
  color: string;
  settings: GroupSettings;
  config: ConfigResponse;
}

function buildSubtitle(settings: GroupSettings): string {
  const names = settings.selectedDatasets;
  if (!names.length) return "No datasets selected";
  let label = names.join(" + ");
  if (names.length > 1) label += ` (${settings.combineMethod})`;
  const methodStr = settings.method === "freq" ? "Freq" : "Imp";
  const geoStr    = settings.geo === "nat" ? "National" : "Utah";
  const aggMap: Record<string, string> = {
    major: "Major Category", minor: "Minor Category",
    broad: "Broad Occupation", occupation: "Occupation",
  };
  const extras: string[] = [];
  if (settings.useAutoAug) extras.push("auto-aug");
  if (settings.physicalMode !== "all") extras.push(settings.physicalMode);
  const extrasStr = extras.length ? `  ·  ${extras.join(", ")}` : "";
  return `${label}  ·  ${methodStr}  ·  ${geoStr}  ·  ${aggMap[settings.aggLevel]}${extrasStr}  ·  Top ${settings.topN}`;
}

export default function GroupPanel({ groupId, color, settings, config }: Props) {
  const [rows, setRows]     = useState<ChartRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState<string | null>(null);

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

  const subtitle = buildSubtitle(settings);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, width: "100%", minWidth: 0 }}>
      {/* Group header */}
      <div style={{ backgroundColor: color, borderRadius: 8, padding: "10px 16px", color: "white", fontSize: 14, fontWeight: 700, letterSpacing: "-0.01em" }}>
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
          {[
            { metric: "workers" as const },
            { metric: "wages"   as const },
            { metric: "tasks"   as const },
          ].map(({ metric }) => (
            <div key={metric} style={{ background: "var(--bg-surface)", borderRadius: 10, border: "1px solid var(--border)", padding: "4px 8px 8px", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
              <HorizontalBarChart rows={rows ?? []} metric={metric} color={color} subtitle={subtitle} />
            </div>
          ))}
        </>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
