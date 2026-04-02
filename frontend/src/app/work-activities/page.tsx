"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { WorkActivitiesResponse, ConfigResponse, ActivityGroup } from "@/lib/types";
import { fetchConfig, fetchWorkActivities } from "@/lib/api";
import { getLatestDataset } from "@/lib/datasetRules";
import DatasetSelector from "@/components/DatasetSelector";
import WorkActivitiesPanel from "@/components/WorkActivitiesPanel";
import { GROUP_A_COLOR, GROUP_B_COLOR } from "@/lib/theme";
import { useSimpleMode } from "@/lib/SimpleModeContext";

// ── Types ──────────────────────────────────────────────────────────────────────

interface WAGroupPending {
  dataset:       string;
  method:        "freq" | "imp";
  geo:           string;
  activityLevel: "gwa" | "iwa" | "dwa";
  topN:          number;
  sortBy:        string;
  physicalMode:  "all" | "exclude" | "only";
  useAutoAug:    boolean;
  searchQuery:   string;
  contextSize:   number;
}

function pendingToConfigSummary(p: WAGroupPending, groupId: "A" | "B"): string[] {
  const dsLabel = p.dataset || "None";
  const physLabel = p.physicalMode === "all" ? "All tasks" : p.physicalMode === "exclude" ? "Non-physical only" : "Physical only";
  const augLabel  = p.useAutoAug ? "Auto-aug: On" : "Auto-aug: Off";
  const line1 = `Group ${groupId}  ·  Dataset: ${dsLabel}  ·  Activity: ${p.activityLevel.toUpperCase()}  ·  Method: ${p.method === "freq" ? "Time" : "Value"}  ·  Geo: ${p.geo}`;
  const line2 = `${physLabel}  ·  ${augLabel}  ·  Top ${p.topN}  ·  Sort: ${p.sortBy}${p.searchQuery ? `  ·  Search: "${p.searchQuery}"` : ""}`;
  return [line1, line2];
}

function defaultPending(dataset: string): WAGroupPending {
  return {
    dataset,
    method: "freq", geo: "nat",
    activityLevel: "gwa",
    topN: 20, sortBy: "Workers Affected",
    physicalMode: "all", useAutoAug: false,
    searchQuery: "", contextSize: 5,
  };
}

/** In simple mode, override fixed fields */
function applyWASimpleDefaults(p: WAGroupPending, config: ConfigResponse): WAGroupPending {
  const simple = getLatestDataset(config.dataset_categories, "AEI Both") ?? "";
  return {
    ...p,
    dataset: config.dataset_availability[simple] ? simple : "",
    method: "freq",
    physicalMode: "all",
    useAutoAug: true,
  };
}

// Family helpers — AEI and MCP/Microsoft cannot be mixed
function getFamily(datasets: string[]): "aei" | "mcp" | "none" {
  const hasAEI = datasets.some((d) => d.startsWith("AEI"));
  const hasMCP = datasets.some((d) => d.startsWith("MCP") || d === "Microsoft");
  if (hasAEI && !hasMCP) return "aei";
  if (hasMCP && !hasAEI) return "mcp";
  return "none";  // empty or mixed (shouldn't happen with UI enforcement)
}

// ── Shared sub-components ──────────────────────────────────────────────────────

function ControlLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{
      fontSize: 10, fontWeight: 700,
      color: "var(--text-muted)",
      textTransform: "uppercase",
      letterSpacing: "0.08em",
      margin: "0 0 5px",
    }}>
      {children}
    </p>
  );
}

function SegBtn<T extends string>({
  options, value, onChange, padding = "5px 11px",
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  padding?: string;
}) {
  return (
    <div style={{ display: "inline-flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
      {options.map(({ value: v, label }, i) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          style={{
            padding,
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

// ── Info tooltip ───────────────────────────────────────────────────────────────

function InfoTooltip({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  return (
    <div ref={ref} style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
      <span
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: 14, height: 14, borderRadius: "50%",
          background: "var(--border)", color: "var(--text-muted)",
          fontSize: 9, fontWeight: 700, cursor: "default",
          flexShrink: 0, marginLeft: 4,
        }}
      >?</span>
      {show && (
        <div style={{
          position: "fixed",
          zIndex: 9999,
          background: "#1a1a1a", color: "#fff",
          fontSize: 11, lineHeight: 1.5,
          padding: "6px 10px", borderRadius: 6,
          maxWidth: 220, pointerEvents: "none",
          boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
          left: (() => {
            if (!ref.current) return 0;
            const rect = ref.current.getBoundingClientRect();
            const tipW = 220;
            return Math.min(rect.left + 18, window.innerWidth - tipW - 8);
          })(),
          top: (() => {
            if (!ref.current) return 0;
            const rect = ref.current.getBoundingClientRect();
            return rect.top - 4;
          })(),
          transform: "translateY(-100%)",
        }}>{text}</div>
      )}
    </div>
  );
}

// (DatasetPillsWA removed — replaced by DatasetSelector component)

// ── Section header ─────────────────────────────────────────────────────────────

function SectionHead({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, marginTop: 4 }}>
      <p style={{
        fontSize: 12, fontWeight: 700, color: "var(--text-muted)",
        textTransform: "uppercase", letterSpacing: "0.09em",
        margin: 0, whiteSpace: "nowrap",
      }}>{label}</p>
      <div style={{ flex: 1, height: 1, background: "var(--border-light)" }} />
    </div>
  );
}

const SORT_SHORT: Record<string, string> = {
  "Workers Affected": "Workers",
  "Wages Affected":   "Wages",
  "% Tasks Affected": "% Tasks",
};

// ── Group settings panel ───────────────────────────────────────────────────────

function WAGroupSettingsPanel({
  groupId, color, pending, setPending, config, sortOptions,
  collapsed, onToggleCollapse, simpleMode = false,
}: {
  groupId: "A" | "B";
  color: string;
  pending: WAGroupPending;
  setPending: (p: WAGroupPending) => void;
  config: ConfigResponse;
  sortOptions: string[];
  collapsed: boolean;
  onToggleCollapse: () => void;
  simpleMode?: boolean;
}) {
  function set<K extends keyof WAGroupPending>(k: K, v: WAGroupPending[K]) {
    setPending({ ...pending, [k]: v });
  }

  const summaryDs = pending.dataset || "No dataset";
  const summary = [
    summaryDs,
    pending.activityLevel.toUpperCase(),
    pending.method === "freq" ? "Time" : "Value",
    config.geo_options[pending.geo] ?? pending.geo,
    `Sort: ${SORT_SHORT[pending.sortBy] ?? pending.sortBy}`,
    pending.physicalMode !== "all" ? (pending.physicalMode === "exclude" ? "No Phys" : "Phys only") : null,
    pending.useAutoAug ? "Auto-aug On" : null,
  ].filter(Boolean).join(" · ");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>

      {simpleMode ? (
        /* Simple mode: only show activity level, geo, sort */
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <ControlLabel>Activity level</ControlLabel>
            <SegBtn
              options={[{ value: "gwa", label: "GWA" }, { value: "iwa", label: "IWA" }, { value: "dwa", label: "DWA" }]}
              value={pending.activityLevel}
              onChange={(v) => set("activityLevel", v)}
            />
          </div>
          <div>
            <ControlLabel>Geography</ControlLabel>
            <select
              value={pending.geo}
              onChange={(e) => set("geo", e.target.value)}
              style={{ fontSize: 12, padding: "5px 8px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--bg-surface)", color: "var(--text-primary)" }}
            >
              {Object.entries(config.geo_options).map(([code, label]) => (
                <option key={code} value={code}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <ControlLabel>Sort by</ControlLabel>
            <SegBtn
              options={sortOptions.map((opt) => ({ value: opt, label: SORT_SHORT[opt] ?? opt }))}
              value={pending.sortBy}
              onChange={(v) => set("sortBy", v)}
            />
          </div>
        </div>
      ) : !collapsed ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>

          {/* ─ Dataset ─ */}
          <SectionHead label="Dataset" />
          <DatasetSelector
            categories={config.dataset_categories}
            value={pending.dataset}
            onChange={(v) => set("dataset", v)}
            label={`Group ${groupId}`}
          />

          {/* ─ Display ─ */}
          <SectionHead label="Display" />
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Activity level</ControlLabel>
                <InfoTooltip text="GWA: General Work Activities (broadest). IWA: Intermediate Work Activities. DWA: Detailed Work Activities (most granular)." />
              </div>
              <SegBtn
                options={[
                  { value: "gwa", label: "GWA" },
                  { value: "iwa", label: "IWA" },
                  { value: "dwa", label: "DWA" },
                ]}
                value={pending.activityLevel}
                onChange={(v) => set("activityLevel", v)}
              />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Method</ControlLabel>
                <InfoTooltip text="Time: weights tasks by how often they're done (freq_mean). Value: weights by freq × relevance × importance." />
              </div>
              <SegBtn
                options={[{ value: "freq", label: "Time" }, { value: "imp", label: "Value" }]}
                value={pending.method}
                onChange={(v) => set("method", v)}
              />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Geography</ControlLabel>
                <InfoTooltip text="Select which state's BLS OEWS employment and wage figures to use." />
              </div>
              <select
                value={pending.geo}
                onChange={(e) => set("geo", e.target.value)}
                style={{ fontSize: 12, padding: "5px 8px", border: "1px solid var(--border)", borderRadius: 6, background: "var(--bg-surface)", color: "var(--text-primary)" }}
              >
                {Object.entries(config.geo_options).map(([code, label]) => (
                  <option key={code} value={code}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Sort by</ControlLabel>
                <InfoTooltip text="Which metric to sort activities by (descending). Run required to re-sort." />
              </div>
              <SegBtn
                options={sortOptions.map((opt) => ({ value: opt, label: SORT_SHORT[opt] ?? opt }))}
                value={pending.sortBy}
                onChange={(v) => set("sortBy", v)}
              />
            </div>
          </div>

          {/* ─ Filtering ─ */}
          <SectionHead label="Filtering" />
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Tasks</ControlLabel>
                <InfoTooltip text="Filter tasks by physical nature. 'Phys only' includes tasks that require physical presence. 'No Phys' excludes them." />
              </div>
              <SegBtn
                options={[
                  { value: "all",     label: "All"       },
                  { value: "exclude", label: "No Phys"   },
                  { value: "only",    label: "Phys only" },
                ]}
                value={pending.physicalMode}
                onChange={(v) => set("physicalMode", v)}
              />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Auto-aug weight</ControlLabel>
                <InfoTooltip text="When On, multiplies each task's completion weight by its AI automatability score (auto_aug_mean / 5)." />
              </div>
              <SegBtn
                options={[{ value: "false" as never, label: "Off" }, { value: "true" as never, label: "On" }]}
                value={String(pending.useAutoAug) as never}
                onChange={(v) => set("useAutoAug", v === "true")}
                padding="5px 7px"
              />
            </div>

          </div>

          <button
            onClick={onToggleCollapse}
            style={{
              alignSelf: "flex-start", marginTop: 4,
              padding: "3px 10px", fontSize: 11,
              background: "none", border: "1px solid var(--border)",
              borderRadius: 5, color: "var(--text-muted)", cursor: "pointer",
            }}
          >▲ Collapse</button>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 1, minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {summary}
          </span>
          <button
            onClick={onToggleCollapse}
            style={{
              flexShrink: 0, padding: "3px 10px", fontSize: 11,
              background: "none", border: "1px solid var(--border)",
              borderRadius: 5, color: "var(--text-secondary)", cursor: "pointer",
            }}
          >▼ Settings</button>
        </div>
      )}

      {/* Always visible: Search + Top N */}
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end", marginTop: 6 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center" }}>
            <ControlLabel>Search activity</ControlLabel>
            <InfoTooltip text="Find a specific activity. Results center around the match ± context rows. Updates chart immediately." />
          </div>
          <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <input
              type="text"
              placeholder="Search…"
              value={pending.searchQuery}
              onChange={(e) => set("searchQuery", e.target.value)}
              style={{
                fontSize: 12, border: "1px solid var(--border)", borderRadius: 6,
                padding: "5px 8px", background: "var(--bg-surface)", color: "var(--text-primary)",
                width: 140, height: 31, outline: "none",
              }}
              onFocus={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
              onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
            />
            {pending.searchQuery && (
              <button
                onClick={() => set("searchQuery", "")}
                style={{
                  position: "absolute", right: 6,
                  background: "none", border: "none", cursor: "pointer",
                  color: "var(--text-muted)", fontSize: 14, lineHeight: 1, padding: 0,
                }}
              >×</button>
            )}
          </div>
        </div>

        {pending.searchQuery ? (
          <div>
            <div style={{ display: "flex", alignItems: "center" }}>
              <ControlLabel>Context ±</ControlLabel>
              <InfoTooltip text="How many rows above and below the matched activity to show." />
            </div>
            <SegBtn
              options={[{ value: "5" as never, label: "5" }, { value: "10" as never, label: "10" }]}
              value={String(pending.contextSize) as never}
              onChange={(v) => set("contextSize", Number(v))}
            />
          </div>
        ) : (
          <div>
            <div style={{ display: "flex", alignItems: "center" }}>
              <ControlLabel>Top {pending.topN}</ControlLabel>
              <InfoTooltip text="Number of top activities to display. Updates immediately after run." />
            </div>
            <input
              type="range" min={5} max={30} step={1} value={Math.min(pending.topN, 30)}
              onChange={(e) => set("topN", Number(e.target.value))}
              style={{ width: 80, accentColor: "var(--brand)", display: "block", marginTop: 4 }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function WorkActivitiesPage() {
  const { isSimple } = useSimpleMode();
  const [config, setConfig]           = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  const [pendingA, setPendingA] = useState<WAGroupPending>(defaultPending("AEI Both 2026-02-12"));
  const [pendingB, setPendingB] = useState<WAGroupPending>(defaultPending("MCP Cumul. v4"));
  const [activeGroup, setActiveGroup] = useState<"A" | "B">("A");
  const [panelCollapsed, setPanelCollapsed] = useState(false);

  const [responseA, setResponseA] = useState<WorkActivitiesResponse | null>(null);
  const [responseB, setResponseB] = useState<WorkActivitiesResponse | null>(null);
  const [loadingA, setLoadingA]   = useState(false);
  const [loadingB, setLoadingB]   = useState(false);
  const [errorA, setErrorA]       = useState<string | null>(null);
  const [errorB, setErrorB]       = useState<string | null>(null);
  const [appliedPendingA, setAppliedPendingA] = useState<WAGroupPending | null>(null);
  const [appliedPendingB, setAppliedPendingB] = useState<WAGroupPending | null>(null);

  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setConfig(cfg);
        const validDs = (ds: string) => cfg.dataset_availability[ds] ? ds : "";
        setPendingA((p) => ({ ...p, dataset: validDs(p.dataset) }));
        setPendingB((p) => ({ ...p, dataset: validDs(p.dataset) }));
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  const run = useCallback(async () => {
    const effectiveA = isSimple && config ? applyWASimpleDefaults(pendingA, config) : pendingA;
    const effectiveB = pendingB;

    const makeSettings = (p: WAGroupPending) => ({
      selectedDatasets: p.dataset ? [p.dataset] : [],
      combineMethod:    "Average" as const,
      method:           p.method,
      geo:              p.geo,
      aggLevel:         "major" as const,
      topN:             999,
      sortBy:           p.sortBy,
      physicalMode:     p.physicalMode,
      useAutoAug:       p.useAutoAug,
    });

    const fetchGroup = async (
      p: WAGroupPending,
      setError: (e: string | null) => void,
    ): Promise<WorkActivitiesResponse | null> => {
      if (!p.dataset) return null;
      try {
        return await fetchWorkActivities(makeSettings(p));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load work activities");
        return null;
      }
    };

    setAppliedPendingA(effectiveA);
    setAppliedPendingB(effectiveB);
    setLoadingA(true); setErrorA(null);

    if (isSimple) {
      const resA = await fetchGroup(effectiveA, setErrorA);
      setResponseA(resA);
      setResponseB(null);
      setLoadingA(false);
    } else {
      setLoadingB(true); setErrorB(null);
      const [resA, resB] = await Promise.all([
        fetchGroup(effectiveA, setErrorA),
        fetchGroup(effectiveB, setErrorB),
      ]);
      setResponseA(resA);
      setResponseB(resB);
      setLoadingA(false);
      setLoadingB(false);
    }
    setPanelCollapsed(true);
  }, [pendingA, pendingB, isSimple, config]);

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

  const activePending    = activeGroup === "A" ? pendingA : pendingB;
  const setActivePending = activeGroup === "A" ? setPendingA : setPendingB;
  const otherPending     = activeGroup === "A" ? pendingB  : pendingA;
  const activeColor      = activeGroup === "A" ? GROUP_A_COLOR : GROUP_B_COLOR;

  function syncToOther() {
    const copy = { ...activePending };
    if (activeGroup === "A") setPendingB(copy);
    else setPendingA(copy);
  }

  // Full other-group summary
  const physLabelOther = otherPending.physicalMode === "all" ? "All tasks"
    : otherPending.physicalMode === "exclude" ? "No Phys" : "Phys only";
  const augLabelOther = otherPending.useAutoAug ? "Auto-aug On" : "Auto-aug Off";
  const dsLabelOther = otherPending.dataset || "none";

  return (
    <div style={{
      height: "calc(100vh - var(--nav-height))",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* ── Header band ── */}
      <div style={{
        flexShrink: 0,
        background: "var(--bg-header)",
        borderBottom: "1px solid var(--border)",
        padding: "14px 24px 14px",
      }}>
        {/* Page title */}
        <div style={{ marginBottom: 12 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", margin: 0, lineHeight: 1.25 }}>
            Work Activities
          </h1>
          <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "3px 0 0", lineHeight: 1.5 }}>
            AI automation exposure by General, Intermediate, and Detailed Work Activities (O*NET).
          </p>
        </div>

        {/* Group A/B tab toggle + sync (hidden in simple mode) */}
        {!isSimple ? (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
            {(["A", "B"] as const).map((g) => {
              const col = g === "A" ? GROUP_A_COLOR : GROUP_B_COLOR;
              const isActive = activeGroup === g;
              return (
                <button
                  key={g}
                  onClick={() => setActiveGroup(g)}
                  style={{
                    display: "flex", alignItems: "center", gap: 6,
                    padding: "5px 14px",
                    fontSize: 12, fontWeight: isActive ? 700 : 500,
                    background: isActive ? "var(--brand-light)" : "transparent",
                    color: isActive ? "var(--brand)" : "var(--text-secondary)",
                    border: "none",
                    borderRight: g === "A" ? "1px solid var(--border)" : "none",
                    cursor: "pointer",
                    transition: "background 0.12s",
                  }}
                >
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: col }} />
                  Group {g}
                  <span style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 400 }}>
                    ({(g === "A" ? pendingA : pendingB).dataset || "none"})
                  </span>
                </button>
              );
            })}
          </div>

          <button
            onClick={syncToOther}
            title={`Copy Group ${activeGroup} settings to Group ${activeGroup === "A" ? "B" : "A"}`}
            style={{
              display: "flex", alignItems: "center", gap: 5,
              padding: "5px 11px", fontSize: 11, fontWeight: 500,
              background: "var(--bg-surface)", border: "1px solid var(--border)",
              borderRadius: 6, color: "var(--text-secondary)",
              cursor: "pointer", transition: "border-color 0.12s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
            onMouseOut={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
          >
            <span style={{ fontSize: 13 }}>⇄</span>
            Sync to {activeGroup === "A" ? "B" : "A"}
          </button>

          <div style={{ flex: 1 }} />

          <button
            onClick={run}
            className="btn-brand"
            style={{ padding: "7px 24px", fontSize: 13 }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}
          >
            Run
          </button>
        </div>
        ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <div style={{ flex: 1 }} />
          <button
            onClick={run}
            className="btn-brand"
            style={{ padding: "7px 24px", fontSize: 13 }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e)  => (e.currentTarget.style.background = "var(--brand)")}
          >
            Run
          </button>
        </div>
        )}

        {/* Active group settings */}
        <WAGroupSettingsPanel
          groupId={isSimple ? "A" : activeGroup}
          color={isSimple ? GROUP_A_COLOR : activeColor}
          pending={isSimple ? pendingA : activePending}
          setPending={isSimple ? setPendingA : setActivePending}
          config={config}
          sortOptions={config.sort_options}
          collapsed={panelCollapsed}
          onToggleCollapse={() => setPanelCollapsed((c) => !c)}
          simpleMode={isSimple}
        />

        {/* Full other group summary (hidden in simple mode) */}
        {!isSimple && (
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--text-muted)" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            padding: "3px 10px",
            background: "var(--bg-surface)", border: "1px solid var(--border-light)", borderRadius: 4,
            flexWrap: "wrap", rowGap: 2,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: activeGroup === "A" ? GROUP_B_COLOR : GROUP_A_COLOR, flexShrink: 0 }} />
            <strong style={{ fontWeight: 600 }}>Group {activeGroup === "A" ? "B" : "A"}:</strong>&nbsp;
            {dsLabelOther}
            &nbsp;·&nbsp;{otherPending.activityLevel.toUpperCase()}
            &nbsp;·&nbsp;{otherPending.method === "freq" ? "Time" : "Value"}
            &nbsp;·&nbsp;{config.geo_options[otherPending.geo] ?? otherPending.geo}
            &nbsp;·&nbsp;Top {otherPending.topN}
            &nbsp;·&nbsp;Sort: {otherPending.sortBy}
            &nbsp;·&nbsp;{physLabelOther}
            &nbsp;·&nbsp;{augLabelOther}
            {otherPending.searchQuery && `  ·  Search: "${otherPending.searchQuery}"`}
          </span>
        </div>
        )}
      </div>

      {/* ── Chart area ── */}
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
        <div style={{
          padding: "32px 28px 24px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
          gap: 24,
          alignContent: "start",
          flex: 1,
        }}>
          <WorkActivitiesPanel
            groupId="A"
            color={GROUP_A_COLOR}
            response={responseA}
            loading={loadingA}
            error={errorA}
            activityLevel={pendingA.activityLevel}
            searchQuery={pendingA.searchQuery}
            contextSize={pendingA.contextSize}
            topN={pendingA.topN}
            configSummary={appliedPendingA ? pendingToConfigSummary(appliedPendingA, "A") : undefined}
            otherResponse={isSimple ? null : responseB}
            otherActivityLevel={pendingB.activityLevel}
          />
          {!isSimple && (
          <WorkActivitiesPanel
            groupId="B"
            color={GROUP_B_COLOR}
            response={responseB}
            loading={loadingB}
            error={errorB}
            activityLevel={pendingB.activityLevel}
            searchQuery={pendingB.searchQuery}
            contextSize={pendingB.contextSize}
            topN={pendingB.topN}
            configSummary={appliedPendingB ? pendingToConfigSummary(appliedPendingB, "B") : undefined}
            otherResponse={responseA}
            otherActivityLevel={pendingA.activityLevel}
          />
          )}
        </div>

        {/* Footer spacer */}
        <div style={{ height: 20, marginTop: "auto" }} />
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
