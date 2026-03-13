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

function Radio({
  label,
  options,
  value,
  onChange,
  horizontal = false,
}: {
  label: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
  horizontal?: boolean;
}) {
  return (
    <div className="mb-3">
      <p className="text-xs font-semibold text-gray-600 mb-1">{label}</p>
      <div className={horizontal ? "flex gap-3 flex-wrap" : "flex flex-col gap-1"}>
        {options.map((opt) => (
          <label key={opt} className="flex items-center gap-1.5 cursor-pointer text-xs">
            <input
              type="radio"
              name={`${label}-${opt}`}
              checked={value === opt}
              onChange={() => onChange(opt)}
              className="accent-current"
            />
            {opt}
          </label>
        ))}
      </div>
    </div>
  );
}

function Checkbox({
  label,
  checked,
  onChange,
  help,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  help?: string;
}) {
  return (
    <label className="flex items-start gap-2 cursor-pointer mb-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 accent-current"
      />
      <span className="text-xs text-gray-700">
        {label}
        {help && <span className="block text-gray-400 text-xs mt-0.5">{help}</span>}
      </span>
    </label>
  );
}

const AGG_DISPLAY_LABELS: Record<string, string> = {
  major: "Major Category",
  minor: "Minor Category",
  broad: "Broad Occupation",
  occupation: "Occupation",
};

const AGG_INTERNAL: Record<string, GroupSettings["aggLevel"]> = {
  "Major Category": "major",
  "Minor Category": "minor",
  "Broad Occupation": "broad",
  Occupation: "occupation",
};

export default function GroupSettings({ groupId, color, settings, config, onChange }: Props) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const hasAei = settings.selectedDatasets.some((n) =>
    ["AEI v1", "AEI v2", "AEI v3", "AEI v4", "AEI API v3", "AEI API v4", "Eco 2015"].includes(n)
  );
  const hasMcp = settings.selectedDatasets.some((n) => n.startsWith("MCP"));

  const update = (patch: Partial<GroupSettings>) =>
    onChange({ ...settings, ...patch });

  const maxN = settings.aggLevel === "occupation" ? 50 : 30;

  return (
    <div>
      {/* Group header */}
      <div
        className="rounded px-3 py-1.5 mb-3 text-white text-sm font-bold"
        style={{ backgroundColor: color }}
      >
        Group {groupId}
      </div>

      {/* Dataset multi-select */}
      <div className="mb-3">
        <p className="text-xs font-semibold text-gray-600 mb-1">Datasets</p>
        <div className="flex flex-col gap-1 max-h-48 overflow-y-auto pr-1">
          {config.datasets.map((name) => {
            const available = config.dataset_availability[name];
            return (
              <label key={name} className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.selectedDatasets.includes(name)}
                  disabled={!available}
                  onChange={(e) => {
                    const next = e.target.checked
                      ? [...settings.selectedDatasets, name]
                      : settings.selectedDatasets.filter((d) => d !== name);
                    update({ selectedDatasets: next });
                  }}
                  className="accent-current"
                />
                <span
                  className={`text-xs ${available ? "text-gray-700" : "text-gray-400 line-through"}`}
                >
                  {name}
                  {!available && " (missing)"}
                </span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Combine method — only if >1 dataset */}
      {settings.selectedDatasets.length > 1 && (
        <Radio
          label="Combine multiple datasets by"
          options={["Average", "Max"]}
          value={settings.combineMethod}
          onChange={(v) => update({ combineMethod: v as "Average" | "Max" })}
          horizontal
        />
      )}

      {/* Task completion method */}
      <Radio
        label="Task completion method"
        options={["Frequency", "Importance-weighted"]}
        value={settings.method === "freq" ? "Frequency" : "Importance-weighted"}
        onChange={(v) => update({ method: v === "Frequency" ? "freq" : "imp" })}
        horizontal
      />

      {/* Geography */}
      <Radio
        label="Geography"
        options={["National", "Utah"]}
        value={settings.geo === "nat" ? "National" : "Utah"}
        onChange={(v) => update({ geo: v === "National" ? "nat" : "ut" })}
        horizontal
      />

      {/* Aggregation level */}
      <Radio
        label="Aggregation level"
        options={Object.keys(AGG_INTERNAL)}
        value={AGG_DISPLAY_LABELS[settings.aggLevel]}
        onChange={(v) => {
          const newAgg = AGG_INTERNAL[v];
          const newMax = newAgg === "occupation" ? 50 : 30;
          update({ aggLevel: newAgg, topN: Math.min(settings.topN, newMax) });
        }}
      />

      {/* Top N */}
      <div className="mb-3">
        <p className="text-xs font-semibold text-gray-600 mb-1">
          Top N to display: <span className="font-bold">{settings.topN}</span>
        </p>
        <input
          type="range"
          min={5}
          max={maxN}
          step={1}
          value={settings.topN}
          onChange={(e) => update({ topN: Number(e.target.value) })}
          className="w-full accent-current"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
          <span>5</span>
          <span>{maxN}</span>
        </div>
      </div>

      {/* Sort by */}
      <div className="mb-3">
        <p className="text-xs font-semibold text-gray-600 mb-1">Rank by</p>
        <select
          value={settings.sortBy}
          onChange={(e) => update({ sortBy: e.target.value })}
          className="w-full text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        >
          {config.sort_options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>

      {/* Advanced Options */}
      <div className="border border-gray-200 rounded">
        <button
          onClick={() => setAdvancedOpen((o) => !o)}
          className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50"
        >
          <span>⚙ Advanced Options</span>
          <span>{advancedOpen ? "▲" : "▼"}</span>
        </button>
        {advancedOpen && (
          <div className="px-3 pb-3 pt-2 border-t border-gray-100">
            <Radio
              label="Physical tasks"
              options={["Include all", "Exclude physical", "Only physical"]}
              value={
                settings.physicalMode === "all"
                  ? "Include all"
                  : settings.physicalMode === "exclude"
                  ? "Exclude physical"
                  : "Only physical"
              }
              onChange={(v) =>
                update({
                  physicalMode:
                    v === "Include all"
                      ? "all"
                      : v === "Exclude physical"
                      ? "exclude"
                      : "only",
                })
              }
            />

            <div className="border-t border-gray-100 my-2" />

            <Checkbox
              label="Apply auto-aug multiplier"
              checked={settings.useAutoAug}
              onChange={(v) => update({ useAutoAug: v, useAdjMean: v ? settings.useAdjMean : false })}
              help="Multiply task completion by auto_aug_mean / 5."
            />

            {hasMcp && settings.useAutoAug && (
              <Checkbox
                label="Use adjusted auto-aug mean for MCP"
                checked={settings.useAdjMean}
                onChange={(v) => update({ useAdjMean: v })}
                help="Uses auto_aug_mean_adj which excludes flagged MCP ratings."
              />
            )}

            {hasAei && !config.crosswalk_available && (
              <div className="mt-2 text-xs bg-yellow-50 border border-yellow-200 rounded p-2 text-yellow-800">
                AEI / Eco 2015 datasets require the SOC 2010→2019 crosswalk file.
                Add <code>2010_to_2019_soc_crosswalk.csv</code> to <code>data/</code>.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
