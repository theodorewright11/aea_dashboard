"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { WorkActivitiesResponse, ConfigResponse } from "@/lib/types";
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
  const line1 = `Group ${groupId}  ·  Datasets: ${dsLabel}  ·  Activity: ${p.activityLevel.toUpperCase()}  ·  Method: ${p.method === "freq" ? "Frequency" : "Importance"}  ·  Geo: ${p.geo === "nat" ? "National" : "Utah"}`;
  const physLabel = p.physicalMode === "all" ? "All tasks" : p.physicalMode === "exclude" ? "Non-physical only" : "Physical only";
  const augLabel  = p.useAutoAug ? `Auto-aug: On${p.useAdjMean ? " (adj)" : ""}` : "Auto-aug: Off";
  const line2 = `${physLabel}  ·  ${augLabel}  ·  Top ${p.topN}${p.searchQuery ? `  ·  Search: "${p.searchQuery}"` : ""}`;
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

// Mutual exclusivity helpers
function isMixed(ds: string[]) {
  const hasAEI = ds.some((d) => d.startsWith("AEI"));
  const hasMCP = ds.some((d) => d.startsWith("MCP") || d === "Microsoft");
  return hasAEI && hasMCP;
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
  options, value, onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 6, overflow: "hidden" }}>
      {options.map(({ value: v, label }, i) => (
        <button
          key={v}
          onClick={() => onChange(v)}
          style={{
            padding: "5px 10px",
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

function DatasetDropdown({
  label, color, datasets, availability, selected, combineMethod, onChange, onChangeCombine,
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
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [open]);

  const summary = selected.length === 0 ? "None"
    : selected.length === 1 ? selected[0]
    : `${selected.length} datasets`;

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <ControlLabel>{label}</ControlLabel>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 6,
          background: "var(--bg-surface)", border: "1px solid var(--border)",
          borderRadius: 7, padding: "5px 10px",
          fontSize: 12, fontWeight: 500, color: "var(--text-primary)",
          cursor: "pointer", whiteSpace: "nowrap", minWidth: 132,
          transition: "border-color 0.12s",
        }}
        onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
        onMouseOut={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
      >
        <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
        <span style={{ flex: 1, textAlign: "left" as const }}>{summary}</span>
        <span style={{ fontSize: 9, color: "var(--text-muted)" }}>▾</span>
      </button>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, zIndex: 200,
          background: "var(--bg-surface)", border: "1px solid var(--border)",
          borderRadius: 8, padding: "8px", minWidth: 192,
          boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
        }}>
          {datasets.map((name) => {
            const avail = availability[name];
            return (
              <label
                key={name}
                style={{
                  display: "flex", alignItems: "center", gap: 7,
                  padding: "4px 6px", cursor: avail ? "pointer" : "default", borderRadius: 4,
                }}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(name)}
                  disabled={!avail}
                  onChange={(e) => {
                    const next = e.target.checked ? [...selected, name] : selected.filter((d) => d !== name);
                    onChange(next);
                  }}
                  style={{ accentColor: color, flexShrink: 0 }}
                />
                <span style={{
                  fontSize: 12,
                  color: avail ? "var(--text-primary)" : "var(--text-muted)",
                  textDecoration: avail ? "none" : "line-through",
                }}>
                  {name}{!avail ? " (unavailable)" : ""}
                </span>
              </label>
            );
          })}
          {selected.length > 1 && (
            <>
              <div style={{ borderTop: "1px solid var(--border-light)", margin: "6px 0" }} />
              <div style={{ padding: "0 6px 2px" }}>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 5px" }}>
                  Combine by
                </p>
                <div style={{ display: "flex", gap: 5 }}>
                  {(["Average", "Max"] as const).map((v) => (
                    <button
                      key={v}
                      onClick={() => onChangeCombine(v)}
                      style={{
                        padding: "3px 9px", fontSize: 11, borderRadius: 5,
                        border: `1.5px solid ${combineMethod === v ? "var(--brand)" : "var(--border)"}`,
                        background: combineMethod === v ? "var(--brand-light)" : "transparent",
                        color: combineMethod === v ? "var(--brand)" : "var(--text-secondary)",
                        cursor: "pointer", fontWeight: combineMethod === v ? 600 : 400,
                        transition: "all 0.1s",
                      }}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Group settings panel ───────────────────────────────────────────────────────

function WAGroupSettingsPanel({
  groupId, color, pending, setPending, config,
}: {
  groupId: "A" | "B";
  color: string;
  pending: WAGroupPending;
  setPending: (p: WAGroupPending) => void;
  config: ConfigResponse;
}) {
  const hasMCP  = pending.datasets.some((d) => d.startsWith("MCP"));
  const mixed   = isMixed(pending.datasets);

  function set<K extends keyof WAGroupPending>(k: K, v: WAGroupPending[K]) {
    setPending({ ...pending, [k]: v });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Mutual exclusivity warning */}
      {mixed && (
        <div style={{
          background: "#fffbeb", border: "1px solid #fbbf24",
          borderRadius: 7, padding: "6px 12px",
          fontSize: 12, color: "#92400e",
          display: "flex", alignItems: "center", gap: 6,
        }}>
          <span>⚠</span>
          <span>AEI-family and MCP/Microsoft cannot be combined in the same group — they use different ECO baselines.</span>
        </div>
      )}

      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>

        <DatasetDropdown
          label={`Group ${groupId} datasets`}
          color={color}
          datasets={config.datasets}
          availability={config.dataset_availability}
          selected={pending.datasets}
          combineMethod={pending.combineMethod}
          onChange={(v) => set("datasets", v)}
          onChangeCombine={(v) => set("combineMethod", v)}
        />

        <div style={{ width: 1, height: 28, background: "var(--border)", alignSelf: "flex-end", marginBottom: 1 }} />

        {/* Activity level */}
        <div>
          <ControlLabel>Activity level</ControlLabel>
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
          <ControlLabel>Method</ControlLabel>
          <SegBtn
            options={[{ value: "freq", label: "Freq" }, { value: "imp", label: "Imp" }]}
            value={pending.method}
            onChange={(v) => set("method", v)}
          />
        </div>

        <div>
          <ControlLabel>Geography</ControlLabel>
          <SegBtn
            options={[{ value: "nat", label: "National" }, { value: "ut", label: "Utah" }]}
            value={pending.geo}
            onChange={(v) => set("geo", v)}
          />
        </div>

        {/* Search bar */}
        <div>
          <ControlLabel>Search activity</ControlLabel>
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

        {/* Context size or Top N */}
        {pending.searchQuery ? (
          <div>
            <ControlLabel>Context ±</ControlLabel>
            <SegBtn
              options={[{ value: "5" as never, label: "5" }, { value: "10" as never, label: "10" }]}
              value={String(pending.contextSize) as never}
              onChange={(v) => set("contextSize", Number(v))}
            />
          </div>
        ) : (
          <div>
            <ControlLabel>Top {pending.topN}</ControlLabel>
            <input
              type="range" min={5} max={50} step={1} value={pending.topN}
              onChange={(e) => set("topN", Number(e.target.value))}
              style={{ width: 80, accentColor: "var(--brand)", display: "block", marginTop: 4 }}
            />
          </div>
        )}

        <div style={{ width: 1, height: 28, background: "var(--border)", alignSelf: "flex-end", marginBottom: 1 }} />

        {/* Physical mode */}
        <div>
          <ControlLabel>Tasks</ControlLabel>
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

        {/* Auto-aug toggle */}
        <div>
          <ControlLabel>Auto-aug weight</ControlLabel>
          <SegBtn
            options={[{ value: "false" as never, label: "Off" }, { value: "true" as never, label: "On" }]}
            value={String(pending.useAutoAug) as never}
            onChange={(v) => set("useAutoAug", v === "true")}
          />
        </div>

        {/* Adj mean — only when MCP selected and auto-aug on */}
        {hasMCP && pending.useAutoAug && (
          <div>
            <ControlLabel>MCP adj mean</ControlLabel>
            <SegBtn
              options={[{ value: "false" as never, label: "Off" }, { value: "true" as never, label: "On" }]}
              value={String(pending.useAdjMean) as never}
              onChange={(v) => set("useAdjMean", v === "true")}
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
      topN:             p.topN,
      sortBy:           p.sortBy,
      physicalMode:     p.physicalMode,
      useAutoAug:       p.useAutoAug,
      useAdjMean:       p.useAdjMean,
    });

    const fetchGroup = async (
      p: WAGroupPending,
      setError: (e: string | null) => void,
    ): Promise<WorkActivitiesResponse | null> => {
      if (isMixed(p.datasets)) {
        setError("Cannot mix AEI and MCP/Microsoft datasets in the same group — they use different ECO baselines.");
        return null;
      }
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

          {/* Sync button */}
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
        />

        {/* Other group summary */}
        <div style={{ marginTop: 8, fontSize: 11, color: "var(--text-muted)" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 4,
            padding: "2px 8px",
            background: "var(--bg-surface)", border: "1px solid var(--border-light)", borderRadius: 4,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: activeGroup === "A" ? GROUP_B_COLOR : GROUP_A_COLOR }} />
            Group {activeGroup === "A" ? "B" : "A"}:&nbsp;
            {otherPending.datasets.length === 0 ? "no datasets"
              : otherPending.datasets.length === 1 ? otherPending.datasets[0]
              : `${otherPending.datasets.length} datasets`}
            &nbsp;·&nbsp;{otherPending.activityLevel.toUpperCase()}
            &nbsp;·&nbsp;{otherPending.method === "freq" ? "Freq" : "Imp"}
            &nbsp;·&nbsp;{otherPending.geo === "nat" ? "National" : "Utah"}
            {otherPending.searchQuery && ` · search: "${otherPending.searchQuery}"`}
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
