"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { WorkActivitiesResponse, ConfigResponse, ActivityGroup } from "@/lib/types";
import { fetchConfig, fetchWorkActivities } from "@/lib/api";
import WorkActivitiesPanel from "@/components/WorkActivitiesPanel";
import { GROUP_A_COLOR, GROUP_B_COLOR } from "@/lib/theme";

// ── Types ──────────────────────────────────────────────────────────────────────

interface WAGroupPending {
  datasets:      string[];
  combineMethod: "Average" | "Max";
  method:        "freq" | "imp";
  geo:           "nat" | "ut";
  activityLevel: "gwa" | "iwa" | "dwa";
  topN:          number;
  sortBy:        string;
  physicalMode:  "all" | "exclude" | "only";
  useAutoAug:    boolean;
  useAdjMean:    boolean;
  searchQuery:   string;
  contextSize:   number;
}

function pendingToConfigSummary(p: WAGroupPending, groupId: "A" | "B"): string[] {
  const dsLabel = p.datasets.length === 0 ? "None"
    : p.datasets.length === 1 ? p.datasets[0]
    : `${p.datasets.join(", ")} (${p.combineMethod})`;
  const physLabel = p.physicalMode === "all" ? "All tasks" : p.physicalMode === "exclude" ? "Non-physical only" : "Physical only";
  const augLabel  = p.useAutoAug ? `Auto-aug: On${p.useAdjMean ? " (adj)" : ""}` : "Auto-aug: Off";
  const line1 = `Group ${groupId}  ·  Datasets: ${dsLabel}  ·  Activity: ${p.activityLevel.toUpperCase()}  ·  Method: ${p.method === "freq" ? "Frequency" : "Importance"}  ·  Geo: ${p.geo === "nat" ? "National" : "Utah"}`;
  const line2 = `${physLabel}  ·  ${augLabel}  ·  Top ${p.topN}  ·  Sort: ${p.sortBy}${p.searchQuery ? `  ·  Search: "${p.searchQuery}"` : ""}`;
  return [line1, line2];
}

function defaultPending(datasets: string[]): WAGroupPending {
  return {
    datasets, combineMethod: "Average",
    method: "freq", geo: "nat",
    activityLevel: "gwa",
    topN: 20, sortBy: "Workers Affected",
    physicalMode: "all", useAutoAug: false, useAdjMean: false,
    searchQuery: "", contextSize: 5,
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

function isAEIFamily(name: string) { return name.startsWith("AEI"); }
function isMCPFamily(name: string) { return name.startsWith("MCP") || name === "Microsoft"; }

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
  options, value, onChange, padding = "5px 10px",
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  padding?: string;
}) {
  return (
    <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 6, overflow: "hidden" }}>
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

// ── Dataset pills with family mutual exclusivity ───────────────────────────────

function DatasetPillsWA({
  label, color, datasets, availability, selected, combineMethod,
  onChange, onChangeCombine,
}: {
  label: string;
  color: string;
  datasets: string[];
  availability: Record<string, boolean>;
  selected: string[];
  combineMethod: "Average" | "Max";
  onChange: (v: string[]) => void;
  onChangeCombine: (v: "Average" | "Max") => void;
}) {
  // Determine which family is currently locked in
  const activeFamily = getFamily(selected);

  function toggle(name: string) {
    if (selected.includes(name)) {
      onChange(selected.filter((d) => d !== name));
    } else {
      // If adding would mix families, clear the other family first
      const newSelected = [...selected, name];
      const hasAEI = newSelected.some(isAEIFamily);
      const hasMCP = newSelected.some(isMCPFamily);
      if (hasAEI && hasMCP) {
        // Adding this dataset would mix — keep only same family
        if (isAEIFamily(name)) onChange(newSelected.filter((d) => !isMCPFamily(d)));
        else onChange(newSelected.filter((d) => !isAEIFamily(d)));
      } else {
        onChange(newSelected);
      }
    }
  }

  // Show note when a family is active
  const familyNote = activeFamily === "aei"
    ? "AEI selected — MCP/Microsoft hidden (different ECO baseline)"
    : activeFamily === "mcp"
    ? "MCP/Microsoft selected — AEI hidden (different ECO baseline)"
    : null;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 5 }}>
        <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", margin: 0 }}>
          {label}
        </p>
        <InfoTooltip text="AEI and MCP/Microsoft cannot be mixed — they use different ECO baselines. Selecting one family hides the other." />
        <button
          disabled={activeFamily === "none"}
          onClick={() => {
            const avail = datasets.filter((d) => availability[d]);
            if (activeFamily === "aei") onChange(avail.filter(isAEIFamily));
            else if (activeFamily === "mcp") onChange(avail.filter(isMCPFamily));
          }}
          style={{ fontSize: 10, color: activeFamily !== "none" ? "var(--brand)" : "var(--text-muted)", background: "none", border: "none", cursor: activeFamily !== "none" ? "pointer" : "default", padding: "0 2px", fontWeight: 600, opacity: activeFamily !== "none" ? 1 : 0.4 }}
        >All</button>
        <button onClick={() => onChange([])} style={{ fontSize: 10, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: "0 2px" }}>None</button>
        {selected.length > 1 && (
          <>
            <span style={{ width: 1, height: 12, background: "var(--border)", display: "inline-block" }} />
            {(["Average", "Max"] as const).map((v) => (
              <button
                key={v}
                onClick={() => onChangeCombine(v)}
                style={{
                  fontSize: 10, padding: "2px 7px", borderRadius: 4,
                  border: `1.5px solid ${combineMethod === v ? "var(--brand)" : "var(--border)"}`,
                  background: combineMethod === v ? "var(--brand-light)" : "transparent",
                  color: combineMethod === v ? "var(--brand)" : "var(--text-secondary)",
                  cursor: "pointer", fontWeight: combineMethod === v ? 600 : 400,
                }}
              >{v}</button>
            ))}
          </>
        )}
      </div>
      {familyNote && (
        <p style={{ fontSize: 10, color: "var(--text-muted)", margin: "0 0 5px", fontStyle: "italic" }}>
          {familyNote}
        </p>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
        {datasets.map((name) => {
          const avail = availability[name];
          const active = selected.includes(name);
          // Hide datasets from the other family when one family is locked in
          const hidden = (activeFamily === "aei" && isMCPFamily(name)) ||
                         (activeFamily === "mcp" && isAEIFamily(name));
          if (hidden) return null;
          return (
            <button
              key={name}
              onClick={() => avail && toggle(name)}
              style={{
                fontSize: 11, padding: "4px 9px", borderRadius: 6,
                border: `1.5px solid ${active ? color : "var(--border)"}`,
                background: active ? color + "18" : "transparent",
                color: active ? color : avail ? "var(--text-secondary)" : "var(--text-muted)",
                cursor: avail ? "pointer" : "default",
                fontWeight: active ? 600 : 400,
                textDecoration: avail ? "none" : "line-through",
                transition: "all 0.12s", whiteSpace: "nowrap",
              }}
            >{name}</button>
          );
        })}
      </div>
    </div>
  );
}

// ── Section header ─────────────────────────────────────────────────────────────

function SectionHead({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, marginTop: 4 }}>
      <p style={{
        fontSize: 9, fontWeight: 700, color: "var(--text-muted)",
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
  collapsed, onToggleCollapse,
}: {
  groupId: "A" | "B";
  color: string;
  pending: WAGroupPending;
  setPending: (p: WAGroupPending) => void;
  config: ConfigResponse;
  sortOptions: string[];
  collapsed: boolean;
  onToggleCollapse: () => void;
}) {
  const hasMCP  = pending.datasets.some((d) => d.startsWith("MCP"));

  function set<K extends keyof WAGroupPending>(k: K, v: WAGroupPending[K]) {
    setPending({ ...pending, [k]: v });
  }

  const summaryDs = pending.datasets.length === 0 ? "No datasets"
    : pending.datasets.length === 1 ? pending.datasets[0]
    : `${pending.datasets.length} ds (${pending.combineMethod})`;
  const summary = [
    summaryDs,
    pending.activityLevel.toUpperCase(),
    pending.method === "freq" ? "Freq" : "Imp",
    pending.geo === "nat" ? "National" : "Utah",
    `Sort: ${SORT_SHORT[pending.sortBy] ?? pending.sortBy}`,
    pending.physicalMode !== "all" ? (pending.physicalMode === "exclude" ? "No Phys" : "Phys only") : null,
    pending.useAutoAug ? `Auto-aug On${pending.useAdjMean ? " (adj)" : ""}` : null,
  ].filter(Boolean).join(" · ");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>

      {!collapsed ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>

          {/* ─ Datasets ─ */}
          <SectionHead label="Datasets" />
          <DatasetPillsWA
            label={`Group ${groupId} datasets`}
            color={color}
            datasets={config.datasets}
            availability={config.dataset_availability}
            selected={pending.datasets}
            combineMethod={pending.combineMethod}
            onChange={(v) => set("datasets", v)}
            onChangeCombine={(v) => set("combineMethod", v)}
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
                <InfoTooltip text="Frequency: weights tasks by how often they're done (freq_mean). Importance: weights by relevance × 2^importance." />
              </div>
              <SegBtn
                options={[{ value: "freq", label: "Freq" }, { value: "imp", label: "Imp" }]}
                value={pending.method}
                onChange={(v) => set("method", v)}
              />
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center" }}>
                <ControlLabel>Geography</ControlLabel>
                <InfoTooltip text="National: uses BLS OEWS national employment and wages. Utah: uses Utah-specific employment and wages." />
              </div>
              <SegBtn
                options={[{ value: "nat", label: "National" }, { value: "ut", label: "Utah" }]}
                value={pending.geo}
                onChange={(v) => set("geo", v)}
              />
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

            {hasMCP && pending.useAutoAug && (
              <div>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <ControlLabel>MCP adj mean</ControlLabel>
                  <InfoTooltip text="Use auto_aug_mean_adj for MCP datasets, which excludes flagged/unreliable ratings." />
                </div>
                <SegBtn
                  options={[{ value: "false" as never, label: "Off" }, { value: "true" as never, label: "On" }]}
                  value={String(pending.useAdjMean) as never}
                  onChange={(v) => set("useAdjMean", v === "true")}
                  padding="5px 7px"
                />
              </div>
            )}
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
  const [config, setConfig]           = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  const [pendingA, setPendingA] = useState<WAGroupPending>(defaultPending(["AEI v4"]));
  const [pendingB, setPendingB] = useState<WAGroupPending>(defaultPending(["MCP v4"]));
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
        const avail = cfg.datasets.filter((d) => cfg.dataset_availability[d]);
        setPendingA((p) => ({ ...p, datasets: p.datasets.filter((d) => avail.includes(d)) }));
        setPendingB((p) => ({ ...p, datasets: p.datasets.filter((d) => avail.includes(d)) }));
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  const run = useCallback(async () => {
    const makeSettings = (p: WAGroupPending) => ({
      selectedDatasets: p.datasets,
      combineMethod:    p.combineMethod,
      method:           p.method,
      geo:              p.geo,
      aggLevel:         "major" as const,
      topN:             999,   // fetch all; topN applied client-side in WorkActivitiesPanel
      sortBy:           p.sortBy,
      physicalMode:     p.physicalMode,
      useAutoAug:       p.useAutoAug,
      useAdjMean:       p.useAdjMean,
    });

    const fetchGroup = async (
      p: WAGroupPending,
      setError: (e: string | null) => void,
    ): Promise<WorkActivitiesResponse | null> => {
      if (!p.datasets.length) return null;
      try {
        return await fetchWorkActivities(makeSettings(p));
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load work activities");
        return null;
      }
    };

    setAppliedPendingA(pendingA);
    setAppliedPendingB(pendingB);
    setLoadingA(true); setErrorA(null);
    setLoadingB(true); setErrorB(null);

    const [resA, resB] = await Promise.all([
      fetchGroup(pendingA, setErrorA),
      fetchGroup(pendingB, setErrorB),
    ]);

    setResponseA(resA);
    setResponseB(resB);
    setLoadingA(false);
    setLoadingB(false);
    setPanelCollapsed(true);
  }, [pendingA, pendingB]);

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
  const augLabelOther = otherPending.useAutoAug
    ? `Auto-aug On${otherPending.useAdjMean ? " (adj)" : ""}` : "Auto-aug Off";
  const dsLabelOther = otherPending.datasets.length === 0 ? "none"
    : otherPending.datasets.length === 1 ? otherPending.datasets[0]
    : `${otherPending.datasets.length} datasets (${otherPending.combineMethod})`;

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
          <h1 style={{ fontSize: 19, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.02em", margin: 0, lineHeight: 1.25 }}>
            Work Activities
          </h1>
          <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "3px 0 0", lineHeight: 1.5 }}>
            AI automation exposure by General, Intermediate, and Detailed Work Activities (O*NET).
          </p>
        </div>

        {/* Group A/B tab toggle + sync */}
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
                    ({(g === "A" ? pendingA : pendingB).datasets.length === 0 ? "none"
                      : (g === "A" ? pendingA : pendingB).datasets.length === 1
                        ? (g === "A" ? pendingA : pendingB).datasets[0]
                        : `${(g === "A" ? pendingA : pendingB).datasets.length} ds`})
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

        {/* Active group settings */}
        <WAGroupSettingsPanel
          groupId={activeGroup}
          color={activeColor}
          pending={activePending}
          setPending={setActivePending}
          config={config}
          sortOptions={config.sort_options}
          collapsed={panelCollapsed}
          onToggleCollapse={() => setPanelCollapsed((c) => !c)}
        />

        {/* Full other group summary */}
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
            &nbsp;·&nbsp;{otherPending.method === "freq" ? "Freq" : "Imp"}
            &nbsp;·&nbsp;{otherPending.geo === "nat" ? "National" : "Utah"}
            &nbsp;·&nbsp;Top {otherPending.topN}
            &nbsp;·&nbsp;Sort: {otherPending.sortBy}
            &nbsp;·&nbsp;{physLabelOther}
            &nbsp;·&nbsp;{augLabelOther}
            {otherPending.searchQuery && `  ·  Search: "${otherPending.searchQuery}"`}
          </span>
        </div>
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
          />
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
          />
        </div>

        {/* Footer */}
        <div style={{ padding: "12px 28px 20px", borderTop: "1px solid var(--border)", marginTop: "auto" }}>
          <p style={{ fontSize: 11, color: "var(--text-muted)", margin: 0 }}>
            Source: 2025 O*NET task data · 2024 BLS OEWS · AEI conversation data · MCP server classification pipeline
          </p>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
