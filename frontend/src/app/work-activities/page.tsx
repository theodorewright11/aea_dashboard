"use client";

import { useEffect, useRef, useState } from "react";
import type { GroupSettings as GroupSettingsType, ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import WorkActivitiesPanel from "@/components/WorkActivitiesPanel";
import { GROUP_A_COLOR, GROUP_B_COLOR } from "@/lib/theme";

// ── Shared control sub-components ─────────────────────────────────────────────

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

  const summary =
    selected.length === 0 ? "None"
    : selected.length === 1 ? selected[0]
    : `${selected.length} datasets`;

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <ControlLabel>{label}</ControlLabel>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 6,
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: 7, padding: "5px 10px",
          fontSize: 12, fontWeight: 500,
          color: "var(--text-primary)",
          cursor: "pointer",
          whiteSpace: "nowrap",
          minWidth: 132,
          transition: "border-color 0.12s",
        }}
        onMouseOver={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
        onMouseOut={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
      >
        <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
        <span style={{ flex: 1, textAlign: "left" as const }}>{summary}</span>
        <span style={{ fontSize: 9, color: "var(--text-muted)" }}>▾</span>
      </button>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, zIndex: 200,
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: 8, padding: "8px",
          minWidth: 192,
          boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
        }}>
          {datasets.map((name) => {
            const avail = availability[name];
            return (
              <label
                key={name}
                style={{
                  display: "flex", alignItems: "center", gap: 7,
                  padding: "4px 6px",
                  cursor: avail ? "pointer" : "default",
                  borderRadius: 4,
                }}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(name)}
                  disabled={!avail}
                  onChange={(e) => {
                    const next = e.target.checked
                      ? [...selected, name]
                      : selected.filter((d) => d !== name);
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
                        padding: "3px 9px", fontSize: 11,
                        borderRadius: 5,
                        border: `1.5px solid ${combineMethod === v ? "var(--brand)" : "var(--border)"}`,
                        background: combineMethod === v ? "var(--brand-light)" : "transparent",
                        color: combineMethod === v ? "var(--brand)" : "var(--text-secondary)",
                        cursor: "pointer",
                        fontWeight: combineMethod === v ? 600 : 400,
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

// ── Default settings ───────────────────────────────────────────────────────────

const DEFAULT_APPLIED_A: GroupSettingsType = {
  selectedDatasets: ["AEI v4"], combineMethod: "Average",
  method: "freq", geo: "nat", aggLevel: "major", topN: 20, sortBy: "Workers Affected",
  useAutoAug: false, useAdjMean: false, physicalMode: "all",
};
const DEFAULT_APPLIED_B: GroupSettingsType = {
  selectedDatasets: ["MCP v4"], combineMethod: "Average",
  method: "freq", geo: "nat", aggLevel: "major", topN: 20, sortBy: "Workers Affected",
  useAutoAug: false, useAdjMean: false, physicalMode: "all",
};

// ── Page ───────────────────────────────────────────────────────────────────────

export default function WorkActivitiesPage() {
  const [config, setConfig]           = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  // Pending (form) state — group-specific
  const [datasetsA, setDatasetsA] = useState<string[]>(["AEI v4"]);
  const [combineA,  setCombineA]  = useState<"Average" | "Max">("Average");
  const [datasetsB, setDatasetsB] = useState<string[]>(["MCP v4"]);
  const [combineB,  setCombineB]  = useState<"Average" | "Max">("Average");

  // Pending (form) state — shared
  const [method, setMethod] = useState<"freq" | "imp">("freq");
  const [geo,    setGeo]    = useState<"nat" | "ut">("nat");

  // Applied (chart) state
  const [appliedA, setAppliedA] = useState<GroupSettingsType>(DEFAULT_APPLIED_A);
  const [appliedB, setAppliedB] = useState<GroupSettingsType>(DEFAULT_APPLIED_B);

  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setConfig(cfg);
        const avail = cfg.datasets.filter((d) => cfg.dataset_availability[d]);
        const filter = (ds: string[]) => ds.filter((d) => avail.includes(d));
        setDatasetsA((prev) => filter(prev));
        setDatasetsB((prev) => filter(prev));
        setAppliedA((prev) => ({ ...prev, selectedDatasets: filter(prev.selectedDatasets) }));
        setAppliedB((prev) => ({ ...prev, selectedDatasets: filter(prev.selectedDatasets) }));
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  function run() {
    const shared = { method, geo, aggLevel: "major" as const, topN: 20, sortBy: "Workers Affected", physicalMode: "all" as const, useAutoAug: false, useAdjMean: false };
    setAppliedA({ ...shared, selectedDatasets: datasetsA, combineMethod: combineA });
    setAppliedB({ ...shared, selectedDatasets: datasetsB, combineMethod: combineB });
  }

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
      {/* ── Header band ── */}
      <div style={{
        flexShrink: 0,
        background: "var(--bg-header)",
        borderBottom: "1px solid var(--border)",
        padding: "18px 24px 16px",
      }}>
        {/* Page title */}
        <div style={{ marginBottom: 14 }}>
          <h1 style={{ fontSize: 19, fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.02em", margin: 0, lineHeight: 1.25 }}>
            Work Activities
          </h1>
          <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "3px 0 0", lineHeight: 1.5 }}>
            AI automation exposure by General, Intermediate, and Detailed Work Activities (O*NET).
          </p>
        </div>

        {/* Config bar */}
        <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "flex-end" }}>

          <DatasetDropdown
            label="Group A"
            color={GROUP_A_COLOR}
            datasets={config.datasets}
            availability={config.dataset_availability}
            selected={datasetsA}
            combineMethod={combineA}
            onChange={setDatasetsA}
            onChangeCombine={setCombineA}
          />

          <DatasetDropdown
            label="Group B"
            color={GROUP_B_COLOR}
            datasets={config.datasets}
            availability={config.dataset_availability}
            selected={datasetsB}
            combineMethod={combineB}
            onChange={setDatasetsB}
            onChangeCombine={setCombineB}
          />

          {/* Visual divider */}
          <div style={{ width: 1, height: 28, background: "var(--border)", alignSelf: "flex-end", marginBottom: 1 }} />

          <div>
            <ControlLabel>Method</ControlLabel>
            <SegBtn
              options={[{ value: "freq", label: "Freq" }, { value: "imp", label: "Imp" }]}
              value={method}
              onChange={setMethod}
            />
          </div>

          <div>
            <ControlLabel>Geography</ControlLabel>
            <SegBtn
              options={[{ value: "nat", label: "National" }, { value: "ut", label: "Utah" }]}
              value={geo}
              onChange={setGeo}
            />
          </div>

          {/* Run button */}
          <button
            onClick={run}
            className="btn-brand"
            style={{ padding: "7px 22px", fontSize: 13, alignSelf: "flex-end" }}
            onMouseOver={(e) => (e.currentTarget.style.background = "var(--brand-hover)")}
            onMouseOut={(e) => (e.currentTarget.style.background = "var(--brand)")}
          >
            Run
          </button>
        </div>
      </div>

      {/* ── Work activity panels ── */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "32px 28px 24px",
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
        gap: 24,
        alignContent: "start",
      }}>
        <WorkActivitiesPanel groupId="A" color={GROUP_A_COLOR} settings={appliedA} />
        <WorkActivitiesPanel groupId="B" color={GROUP_B_COLOR} settings={appliedB} />
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
