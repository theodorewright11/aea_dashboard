"use client";

import { useEffect, useState } from "react";
import type { GroupSettings as GroupSettingsType, ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import WorkActivitiesPanel from "@/components/WorkActivitiesPanel";
import SettingsDrawer from "@/components/SettingsDrawer";
import { GROUP_A_COLOR, GROUP_B_COLOR } from "@/lib/theme";

const DEFAULT_A: GroupSettingsType = {
  selectedDatasets: ["AEI v4"],
  combineMethod: "Average", method: "freq", useAutoAug: false, useAdjMean: false,
  physicalMode: "all", geo: "nat", aggLevel: "major", sortBy: "Workers Affected", topN: 20,
};
const DEFAULT_B: GroupSettingsType = {
  selectedDatasets: ["MCP v4"],
  combineMethod: "Average", method: "freq", useAutoAug: false, useAdjMean: false,
  physicalMode: "all", geo: "nat", aggLevel: "major", sortBy: "Workers Affected", topN: 20,
};

function settingsSummary(s: GroupSettingsType): string {
  const ds = s.selectedDatasets;
  const label =
    ds.length === 0 ? "None"
    : ds.length === 1 ? ds[0]
    : `${ds.length} datasets`;
  const method = s.method === "freq" ? "Freq" : "Imp";
  const geo = s.geo === "nat" ? "Nat" : "Utah";
  return `${label} · ${method} · ${geo}`;
}

function SlidersIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <line x1="3" y1="5"  x2="17" y2="5" />
      <line x1="3" y1="10" x2="17" y2="10" />
      <line x1="3" y1="15" x2="17" y2="15" />
      <circle cx="7"  cy="5"  r="2.2" fill="var(--bg-surface)" stroke="currentColor" strokeWidth="2" />
      <circle cx="13" cy="10" r="2.2" fill="var(--bg-surface)" stroke="currentColor" strokeWidth="2" />
      <circle cx="9"  cy="15" r="2.2" fill="var(--bg-surface)" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export default function WorkActivitiesPage() {
  const [config, setConfig]           = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen]   = useState(false);

  const [pendingA, setPendingA] = useState<GroupSettingsType>(DEFAULT_A);
  const [pendingB, setPendingB] = useState<GroupSettingsType>(DEFAULT_B);
  const [appliedA, setAppliedA] = useState<GroupSettingsType>(DEFAULT_A);
  const [appliedB, setAppliedB] = useState<GroupSettingsType>(DEFAULT_B);

  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setConfig(cfg);
        const available = cfg.datasets.filter((d) => cfg.dataset_availability[d]);
        const filter = (s: GroupSettingsType) => ({
          ...s,
          selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        });
        setPendingA(filter);
        setPendingB(filter);
        setAppliedA(filter);
        setAppliedB(filter);
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  if (configError) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - var(--nav-height))" }}>
        <p style={{ color: "#b91c1c", fontSize: 13 }}>Backend error: {configError}</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - var(--nav-height))" }}>
        <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{
      height: "calc(100vh - var(--nav-height))",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* ── Top bar ── */}
      <div style={{
        flexShrink: 0,
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        gap: 16,
        height: 52,
      }}>
        {/* Page title */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h1 style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.3, letterSpacing: "-0.01em", margin: 0 }}>
            Work Activities
          </h1>
          <p style={{ fontSize: 11, color: "var(--text-muted)", margin: 0, lineHeight: 1.2 }}>
            AI automation exposure by General, Intermediate, and Detailed Work Activities (O*NET).
          </p>
        </div>

        {/* Active settings pills */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
          <span className="pill pill-a">A · {settingsSummary(appliedA)}</span>
          <span className="pill pill-b">B · {settingsSummary(appliedB)}</span>
        </div>

        {/* Configure button */}
        <button
          onClick={() => setDrawerOpen(true)}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: 7,
            padding: "5px 12px",
            fontSize: 12, fontWeight: 500,
            color: "var(--text-secondary)",
            cursor: "pointer",
            flexShrink: 0,
            transition: "all 0.12s",
          }}
          onMouseOver={(e) => { e.currentTarget.style.borderColor = "var(--brand)"; e.currentTarget.style.color = "var(--brand)"; }}
          onMouseOut={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
        >
          <SlidersIcon />
          Configure
        </button>
      </div>

      {/* ── Work activity panels — full width, two-up grid ── */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "28px",
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
        gap: 28,
        alignContent: "start",
      }}>
        <WorkActivitiesPanel groupId="A" color={GROUP_A_COLOR} settings={appliedA} />
        <WorkActivitiesPanel groupId="B" color={GROUP_B_COLOR} settings={appliedB} />
      </div>

      {/* ── Settings drawer ── */}
      <SettingsDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onRun={() => { setAppliedA(pendingA); setAppliedB(pendingB); }}
        pendingA={pendingA}
        pendingB={pendingB}
        onChangeA={setPendingA}
        onChangeB={setPendingB}
        config={config}
      />

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
