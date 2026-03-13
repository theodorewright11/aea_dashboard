"use client";

import { useEffect, useState } from "react";
import type { GroupSettings as GroupSettingsType, ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import GroupSettings from "@/components/GroupSettings";
import GroupPanel from "@/components/GroupPanel";

const DEFAULT_A: GroupSettingsType = {
  selectedDatasets: ["AEI v4"],
  combineMethod: "Average",
  method: "freq",
  useAutoAug: false,
  useAdjMean: false,
  physicalMode: "all",
  geo: "nat",
  aggLevel: "major",
  sortBy: "Workers Affected",
  topN: 10,
};

const DEFAULT_B: GroupSettingsType = {
  selectedDatasets: ["MCP v4"],
  combineMethod: "Average",
  method: "freq",
  useAutoAug: false,
  useAdjMean: false,
  physicalMode: "all",
  geo: "nat",
  aggLevel: "major",
  sortBy: "Workers Affected",
  topN: 10,
};

export default function HomePage() {
  const [config, setConfig]         = useState<ConfigResponse | null>(null);
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
        const filterAvailable = (s: GroupSettingsType) => ({
          ...s,
          selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        });
        setPendingA(filterAvailable);
        setPendingB(filterAvailable);
        setAppliedA(filterAvailable);
        setAppliedB(filterAvailable);
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  if (configError) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
        <div style={{ textAlign: "center", maxWidth: 400 }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
          <p style={{ fontWeight: 600, color: "#b91c1c", marginBottom: 6 }}>Could not connect to backend</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 4 }}>{configError}</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Make sure the FastAPI server is running on{" "}
            <code style={{ background: "#f1f5f9", padding: "1px 4px", borderRadius: 4 }}>
              {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
            </code>
          </p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
        <div style={{ width: 36, height: 36, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const SIDEBAR_W = 272;

  return (
    <div style={{ display: "flex", height: "calc(100vh - 56px)", overflow: "hidden" }}>
      {/* Sidebar */}
      <aside
        style={{
          flexShrink: 0,
          width: sidebarOpen ? SIDEBAR_W : 0,
          overflow: sidebarOpen ? "auto" : "hidden",
          background: "var(--bg-sidebar)",
          borderRight: "1px solid var(--border)",
          transition: "width 0.2s ease",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div style={{ minWidth: SIDEBAR_W, padding: "20px 16px 100px" }}>
          {/* Sidebar header */}
          <div style={{ marginBottom: 20 }}>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>Dashboard Settings</h2>
            <p style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.5 }}>
              Configure each group independently, then click <strong>Run</strong>.
            </p>
          </div>

          <GroupSettings groupId="A" color="#3a5f83" settings={pendingA} config={config} onChange={setPendingA} />

          <div style={{ margin: "20px 0", borderTop: "1px solid var(--border)" }} />

          <GroupSettings groupId="B" color="#4a7c6f" settings={pendingB} config={config} onChange={setPendingB} />
        </div>

        {/* Sticky Run button */}
        <div style={{ position: "sticky", bottom: 0, background: "var(--bg-sidebar)", borderTop: "1px solid var(--border)", padding: "12px 16px", minWidth: SIDEBAR_W }}>
          <button
            onClick={() => { setAppliedA(pendingA); setAppliedB(pendingB); }}
            style={{ width: "100%", background: "var(--brand)", color: "white", border: "none", borderRadius: 8, padding: "10px 0", fontSize: 13, fontWeight: 700, cursor: "pointer", transition: "background 0.15s", letterSpacing: "0.01em" }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e) => (e.currentTarget.style.background = "var(--brand)")}
          >
            Run
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
        {/* Top bar */}
        <div style={{ position: "sticky", top: 0, zIndex: 10, background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "0 24px", display: "flex", alignItems: "center", height: 52, gap: 16 }}>
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-secondary)", fontSize: 18, padding: "4px", borderRadius: 5, display: "flex", alignItems: "center" }}
            title="Toggle sidebar"
          >
            ☰
          </button>
          <div>
            <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3, letterSpacing: "-0.01em" }}>
              Automation Exposure Analysis
            </h1>
            <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Compare automation exposure across datasets, geographies, and aggregation levels.
            </p>
          </div>
        </div>

        {/* Charts */}
        <div style={{ flex: 1, padding: "24px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))", gap: 24, alignContent: "start" }}>
          <GroupPanel groupId="A" color="#3a5f83" settings={appliedA} config={config} />
          <GroupPanel groupId="B" color="#4a7c6f" settings={appliedB} config={config} />
        </div>

        {/* Footer */}
        <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border)", marginTop: "auto" }}>
          <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Source: 2025 O*NET task data · 2024 BLS OEWS · AEI conversation data · MCP server classification pipeline
          </p>
        </div>
      </main>
    </div>
  );
}
