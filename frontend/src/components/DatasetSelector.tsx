"use client";
/**
 * DatasetSelector — Reusable category → sub_type → date picker.
 *
 * Used by chart pages, PctComputePanel, and Task Changes for single-dataset
 * selection. Renders a 3-level cascading selector: category, sub_type, date.
 */
import React from "react";
import type { DatasetCategory } from "@/lib/types";

interface DatasetSelectorProps {
  categories: DatasetCategory[];
  /** Currently selected dataset name (or empty string). */
  value: string;
  /** Called with the new dataset name when selection changes. */
  onChange: (datasetName: string) => void;
  /** Optional: compact styling */
  compact?: boolean;
  /** Optional: label prefix */
  label?: string;
}

/**
 * Resolve a dataset name to its category/subType/date indices.
 */
function resolveSelection(categories: DatasetCategory[], name: string) {
  for (const cat of categories) {
    for (const st of cat.sub_types) {
      for (const ds of st.datasets) {
        if (ds.name === name) {
          return { categoryKey: cat.key, subTypeKey: st.key, date: ds.date };
        }
      }
    }
  }
  return null;
}

export default function DatasetSelector({
  categories,
  value,
  onChange,
  compact,
  label,
}: DatasetSelectorProps) {
  const resolved = resolveSelection(categories, value);

  const selectedCategory = resolved?.categoryKey ?? "";
  const selectedSubType = resolved?.subTypeKey ?? "";
  const selectedDate = resolved?.date ?? "";

  const currentCat = categories.find((c) => c.key === selectedCategory);
  const currentSt = currentCat?.sub_types.find((st) => st.key === selectedSubType);

  const fontSize = compact ? 11 : 12;
  const pad = compact ? "3px 6px" : "5px 8px";
  const selectStyle: React.CSSProperties = {
    fontSize,
    padding: pad,
    border: "1px solid var(--border)",
    borderRadius: 5,
    background: "var(--bg-surface)",
    color: "var(--text-primary)",
    minWidth: 0,
  };

  function handleCategoryChange(catKey: string) {
    const cat = categories.find((c) => c.key === catKey);
    if (!cat || cat.sub_types.length === 0) return;
    const st = cat.sub_types[0];
    const ds = st.datasets[st.datasets.length - 1]; // default to latest date
    if (ds) onChange(ds.name);
  }

  function handleSubTypeChange(stKey: string) {
    const st = currentCat?.sub_types.find((s) => s.key === stKey);
    if (!st) return;
    // Try to keep the same date, or default to latest
    const match = st.datasets.find((d) => d.date === selectedDate);
    const ds = match ?? st.datasets[st.datasets.length - 1];
    if (ds) onChange(ds.name);
  }

  function handleDateChange(date: string) {
    const ds = currentSt?.datasets.find((d) => d.date === date);
    if (ds) onChange(ds.name);
  }

  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
      {label && (
        <span style={{ fontSize, fontWeight: 600, color: "var(--text-secondary)" }}>
          {label}
        </span>
      )}
      {/* Category */}
      <select
        value={selectedCategory}
        onChange={(e) => handleCategoryChange(e.target.value)}
        style={selectStyle}
      >
        {!selectedCategory && <option value="">Select…</option>}
        {categories.map((cat) => (
          <option key={cat.key} value={cat.key}>
            {cat.label}
          </option>
        ))}
      </select>

      {/* Sub-type */}
      {currentCat && currentCat.sub_types.length > 0 && (
        <select
          value={selectedSubType}
          onChange={(e) => handleSubTypeChange(e.target.value)}
          style={selectStyle}
        >
          {currentCat.sub_types.map((st) => (
            <option key={st.key} value={st.key}>
              {st.label}
            </option>
          ))}
        </select>
      )}

      {/* Date */}
      {currentSt && currentSt.datasets.length > 1 && (
        <select
          value={selectedDate}
          onChange={(e) => handleDateChange(e.target.value)}
          style={selectStyle}
        >
          {currentSt.datasets.map((ds) => (
            <option key={ds.date} value={ds.date}>
              {ds.date}
            </option>
          ))}
        </select>
      )}
      {currentSt && currentSt.datasets.length === 1 && (
        <span style={{ fontSize, color: "var(--text-muted)" }}>
          {currentSt.datasets[0].date}
        </span>
      )}
    </div>
  );
}
