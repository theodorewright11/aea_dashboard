"use client";

import { useState } from "react";
import type { GroupSettings, ConfigResponse } from "@/lib/types";

interface Props {
  groupId: "A" | "B";
  color: string;
  settings: GroupSettings;
  config: ConfigResponse;
  onChange: (s: GroupSettings) => void;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>
      {children}
    </p>
  );
}

function RadioGroup({
  label, options, value, onChange, horizontal = false,
}: {
  label: string; options: string[]; value: string;
  onChange: (v: string) => void; horizontal?: boolean;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <SectionLabel>{label}</SectionLabel>
      <div style={{ display: "flex", flexDirection: horizontal ? "row" : "column", gap: horizontal ? 12 : 4, flexWrap: "wrap" }}>
        {options.map((opt) => (
          <label key={opt} style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 12, color: "var(--text-primary)" }}>
            <input type="radio" name={`${label}-${opt}`} checked={value === opt} onChange={() => onChange(opt)}
              style={{ accentColor: "var(--brand)" }} />
            {opt}
          </label>
        ))}
      </div>
    </div>
  );
}

function CheckboxRow({ label, checked, onChange, help }: {
  label: string; checked: boolean; onChange: (v: boolean) => void; help?: string;
}) {
  return (
    <label style={{ display: "flex", alignItems: "flex-start", gap: 8, cursor: "pointer", marginBottom: 8 }}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)}
        style={{ marginTop: 2, accentColor: "var(--brand)" }} />
      <span style={{ fontSize: 12, color: "var(--text-primary)" }}>
        {label}
        {help && <span style={{ display: "block", fontSize: 11, color: "var(--text-muted)", marginTop: 1 }}>{help}</span>}
      </span>
    </label>
  );
}

const AGG_LABELS: Record<string, string> = {
  major: "Major Category", minor: "Minor Category",
  broad: "Broad Occupation", occupation: "Occupation",
};
const AGG_INTERNAL: Record<string, GroupSettings["aggLevel"]> = {
  "Major Category": "major", "Minor Category": "minor",
  "Broad Occupation": "broad", "Occupation": "occupation",
};

export default function GroupSettings({ groupId, color, settings, config, onChange }: Props) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const hasAei = settings.selectedDatasets.some((n) => n.startsWith("AEI"));
  const update = (patch: Partial<GroupSettings>) => onChange({ ...settings, ...patch });
  const maxN = settings.aggLevel === "occupation" ? 50 : 30;

  return (
    <div>
      <div style={{ backgroundColor: color, borderRadius: 8, padding: "7px 12px", marginBottom: 16, color: "white", fontSize: 13, fontWeight: 700 }}>
        Group {groupId}
      </div>

      {/* Datasets */}
      <div style={{ marginBottom: 12 }}>
        <SectionLabel>Datasets</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {config.datasets.map((name) => {
            const available = config.dataset_availability[name];
            return (
              <label key={name} style={{ display: "flex", alignItems: "center", gap: 6, cursor: available ? "pointer" : "default" }}>
                <input type="checkbox"
                  checked={settings.selectedDatasets.includes(name)}
                  disabled={!available}
                  onChange={(e) => {
                    const next = e.target.checked
                      ? [...settings.selectedDatasets, name]
                      : settings.selectedDatasets.filter((d) => d !== name);
                    update({ selectedDatasets: next });
                  }}
                  style={{ accentColor: color }}
                />
                <span style={{ fontSize: 12, color: available ? "var(--text-primary)" : "var(--text-muted)", textDecoration: available ? "none" : "line-through" }}>
                  {name}{!available && " (missing)"}
                </span>
              </label>
            );
          })}
        </div>
      </div>

      {settings.selectedDatasets.length > 1 && (
        <RadioGroup label="Combine datasets by" options={["Average", "Max"]}
          value={settings.combineMethod}
          onChange={(v) => update({ combineMethod: v as "Average" | "Max" })} horizontal />
      )}

      <RadioGroup label="Task completion method" options={["Time", "Value"]}
        value={settings.method === "freq" ? "Time" : "Value"}
        onChange={(v) => update({ method: v === "Time" ? "freq" : "imp" })} horizontal />

      <RadioGroup label="Geography" options={["National", "Utah"]}
        value={settings.geo === "nat" ? "National" : "Utah"}
        onChange={(v) => update({ geo: v === "National" ? "nat" : "ut" })} horizontal />

      <RadioGroup label="Aggregation level" options={Object.keys(AGG_INTERNAL)}
        value={AGG_LABELS[settings.aggLevel]}
        onChange={(v) => {
          const newAgg = AGG_INTERNAL[v];
          update({ aggLevel: newAgg, topN: Math.min(settings.topN, newAgg === "occupation" ? 50 : 30) });
        }} />

      {/* Top N */}
      <div style={{ marginBottom: 12 }}>
        <SectionLabel>Top N: <span style={{ fontWeight: 800, color: "var(--text-primary)", textTransform: "none" }}>{settings.topN}</span></SectionLabel>
        <input type="range" min={5} max={maxN} step={1} value={settings.topN}
          onChange={(e) => update({ topN: Number(e.target.value) })}
          style={{ width: "100%", accentColor: color }} />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
          <span>5</span><span>{maxN}</span>
        </div>
      </div>

      {/* Rank by */}
      <div style={{ marginBottom: 12 }}>
        <SectionLabel>Rank by</SectionLabel>
        <select value={settings.sortBy} onChange={(e) => update({ sortBy: e.target.value })}
          style={{ width: "100%", fontSize: 12, border: "1px solid var(--border)", borderRadius: 6, padding: "5px 8px", background: "var(--bg-surface)", color: "var(--text-primary)" }}>
          {config.sort_options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
        </select>
      </div>

      {/* Advanced */}
      <div style={{ border: "1px solid var(--border)", borderRadius: 8 }}>
        <button onClick={() => setAdvancedOpen((o) => !o)}
          style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 12px", background: "transparent", border: "none", cursor: "pointer", fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          <span>⚙ Advanced</span>
          <span style={{ fontSize: 10 }}>{advancedOpen ? "▲" : "▼"}</span>
        </button>
        {advancedOpen && (
          <div style={{ padding: "8px 12px 12px", borderTop: "1px solid var(--border-light)" }}>
            <RadioGroup label="Physical tasks"
              options={["Include all", "Exclude physical", "Only physical"]}
              value={settings.physicalMode === "all" ? "Include all" : settings.physicalMode === "exclude" ? "Exclude physical" : "Only physical"}
              onChange={(v) => update({ physicalMode: v === "Include all" ? "all" : v === "Exclude physical" ? "exclude" : "only" })} />
            <div style={{ borderTop: "1px solid var(--border-light)", margin: "4px 0 8px" }} />
            <CheckboxRow label="Apply auto-aug multiplier" checked={settings.useAutoAug}
              onChange={(v) => update({ useAutoAug: v })}
              help="Multiply task completion by auto_aug_mean / 5." />
            {hasAei && !config.crosswalk_available && (
              <div style={{ marginTop: 8, fontSize: 11, background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 6, padding: "6px 8px", color: "#92400e" }}>
                AEI datasets require <code>2010_to_2019_soc_crosswalk.csv</code> in <code>data/</code>.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
