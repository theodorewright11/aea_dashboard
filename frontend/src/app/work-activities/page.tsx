"use client";

import { useEffect, useState } from "react";
import type { GroupSettings as GroupSettingsType, ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import GroupSettings from "@/components/GroupSettings";
import WorkActivitiesPanel from "@/components/WorkActivitiesPanel";

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

export default function WorkActivitiesPage() {
  const [config, setConfig]           = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

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
          ...s, selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        });
        setPendingA(filter); setPendingB(filter);
        setAppliedA(filter); setAppliedB(filter);
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  if (configError) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
      <p style={{ color: "#b91c1c" }}>Backend error: {configError}</p>
    </div>
  );

  if (!config) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
      <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  const SIDEBAR_W = 272;

  return (
    <div style={{ display: "flex", height: "calc(100vh - 56px)", overflow: "hidden" }}>
      {/* Sidebar */}
      <aside style={{ flexShrink: 0, width: sidebarOpen ? SIDEBAR_W : 0, overflow: sidebarOpen ? "auto" : "hidden", background: "var(--bg-sidebar)", borderRight: "1px solid var(--border)", transition: "width 0.2s ease", display: "flex", flexDirection: "column" }}>
        <div style={{ minWidth: SIDEBAR_W, padding: "20px 16px 100px" }}>
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Work Activity Settings</h2>
            <p style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.5 }}>
              AEI datasets use the O*NET 2015 task baseline.<br />MCP / Microsoft use the 2025 baseline.
            </p>
          </div>
          <GroupSettings groupId="A" color="#3a5f83" settings={pendingA} config={config} onChange={setPendingA} />
          <div style={{ margin: "20px 0", borderTop: "1px solid var(--border)" }} />
          <GroupSettings groupId="B" color="#4a7c6f" settings={pendingB} config={config} onChange={setPendingB} />
        </div>
        <div style={{ position: "sticky", bottom: 0, background: "var(--bg-sidebar)", borderTop: "1px solid var(--border)", padding: "12px 16px", minWidth: SIDEBAR_W }}>
          <button
            onClick={() => { setAppliedA(pendingA); setAppliedB(pendingB); }}
            style={{ width: "100%", background: "var(--brand)", color: "white", border: "none", borderRadius: 8, padding: "10px 0", fontSize: 13, fontWeight: 700, cursor: "pointer" }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e) => (e.currentTarget.style.background = "var(--brand)")}
          >
            Run
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
        <div style={{ position: "sticky", top: 0, zIndex: 10, background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "0 24px", display: "flex", alignItems: "center", height: 52, gap: 16 }}>
          <button onClick={() => setSidebarOpen((o) => !o)}
            style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-secondary)", fontSize: 18, padding: "4px", borderRadius: 5 }}>
            ☰
          </button>
          <div>
            <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>Work Activities</h1>
            <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
              AI automation exposure by General, Intermediate, and Detailed Work Activities (O*NET).
            </p>
          </div>
        </div>

        <div style={{ flex: 1, padding: "24px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))", gap: 24, alignContent: "start" }}>
          <WorkActivitiesPanel groupId="A" color="#3a5f83" settings={appliedA} />
          <WorkActivitiesPanel groupId="B" color="#4a7c6f" settings={appliedB} />
        </div>
      </main>
    </div>
  );
}
