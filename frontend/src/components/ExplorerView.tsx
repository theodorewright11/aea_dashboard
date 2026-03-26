"use client";

import React, { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import type {
  OccupationSummary,
  TaskDetail,
  TaskSourceStats,
  OccupationTasksResponse,
  ConfigResponse,
  ChartRow,
  ExplorerGroupRow,
  ExplorerGroupsResponse,
  EcoTaskRow,
  McpEntry,
} from "@/lib/types";
import { fetchOccupationTasks, fetchCompute, fetchAllEcoTasks } from "@/lib/api";
import { useSimpleMode } from "@/lib/SimpleModeContext";
import { enforceDatasetToggle } from "@/lib/datasetRules";

// ── Debounce hook ──────────────────────────────────────────────────────────────

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState<T>(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// ── Props ──────────────────────────────────────────────────────────────────────

interface Props {
  occupations: OccupationSummary[];
  groups: ExplorerGroupsResponse;
  config: ConfigResponse;
}

// ── Formatters ─────────────────────────────────────────────────────────────────

function fmtEmp(v?: number | null): string {
  if (v == null) return "—";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return v.toLocaleString();
}

function fmtWage(v?: number | null): string {
  if (v == null) return "—";
  return `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function fmtPctNorm(v?: number | null): string {
  if (v == null) return "—";
  if (v < 0.0001) return ">.0001%";
  if (v < 0.01) return `${parseFloat(v.toPrecision(1))}%`;
  return `${parseFloat(v.toFixed(4))}%`;
}

function fmtAutoAug(v?: number | null): string {
  if (v == null) return "—";
  return v.toFixed(3);
}

function fmtPctPhys(v?: number | null): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

// ── Column definitions ─────────────────────────────────────────────────────────

interface ColDef {
  key: string;
  label: string;
  tooltip?: string;
  width: number;
  numeric: boolean;
}

const COLUMNS: ColDef[] = [
  { key: "name",         label: "Name",            width: 280, numeric: false },
  { key: "occ",          label: "Occupation",       width: 200, numeric: false, tooltip: "Occupation this task belongs to" },
  { key: "broad_cat",    label: "Broad",            width: 180, numeric: false, tooltip: "Broad occupation" },
  { key: "minor_cat",    label: "Minor",            width: 180, numeric: false, tooltip: "Minor occupation category" },
  { key: "major_cat",    label: "Major",            width: 180, numeric: false, tooltip: "Major occupation category" },
  { key: "dwa_col",      label: "DWA",              width: 200, numeric: false, tooltip: "Detailed Work Activity" },
  { key: "iwa_col",      label: "IWA",              width: 200, numeric: false, tooltip: "Intermediate Work Activity" },
  { key: "gwa_col",      label: "GWA",              width: 200, numeric: false, tooltip: "General Work Activity" },
  { key: "emp",          label: "Emp",              width: 90,  numeric: true,  tooltip: "Total employment (BLS OEWS 2024)" },
  { key: "wage",         label: "Med Wage",         width: 90,  numeric: true,  tooltip: "Median annual wage (BLS OEWS 2024)" },
  { key: "phys_col",     label: "Phys",             width: 52,  numeric: false, tooltip: "Physical task (requires physical presence)" },
  { key: "freq_col",     label: "Freq",             width: 70,  numeric: true,  tooltip: "O*NET task frequency (0\u201310)" },
  { key: "imp_col",      label: "Imp",              width: 70,  numeric: true,  tooltip: "O*NET task importance (0\u20135)" },
  { key: "rel_col",      label: "Rel",              width: 70,  numeric: true,  tooltip: "O*NET task relevance (0\u2013100)" },
  { key: "n_occs",       label: "# Occs",           width: 65,  numeric: true,  tooltip: "Number of unique occupations" },
  { key: "n_tasks",      label: "# Tasks",          width: 65,  numeric: true,  tooltip: "Number of unique tasks" },
  { key: "auto_avg_w",   label: "Auto Avg\u2191",   width: 90,  numeric: true,  tooltip: "Avg of per-task avg auto-aug score across sources (0\u20135). Only tasks with at least one source value." },
  { key: "auto_max_w",   label: "Auto Max\u2191",   width: 90,  numeric: true,  tooltip: "Avg of per-task max auto-aug score across sources (0\u20135). Only tasks with at least one source value." },
  { key: "auto_avg_all", label: "Auto Avg (all)",   width: 100, numeric: true,  tooltip: "Avg of per-task avg auto-aug score (0 for tasks with no value) across ALL tasks." },
  { key: "auto_max_all", label: "Auto Max (all)",   width: 100, numeric: true,  tooltip: "Avg of per-task max auto-aug score (0 for tasks with no value) across ALL tasks." },
  { key: "pct_phys",     label: "% Phys",           width: 72,  numeric: true,  tooltip: "Fraction of tasks classified as requiring physical presence." },
  { key: "pct_avg_w",    label: "Pct Avg\u2191",    width: 90,  numeric: true,  tooltip: "Avg of per-task avg pct (share of AI conversations) across sources. Only tasks with a value." },
  { key: "pct_max_w",    label: "Pct Max\u2191",    width: 90,  numeric: true,  tooltip: "Avg of per-task max pct across sources. Only tasks with a value." },
  { key: "pct_avg_all",  label: "Pct Avg (all)",    width: 100, numeric: true,  tooltip: "Avg pct across ALL tasks (0 for tasks with no value)." },
  { key: "pct_max_all",  label: "Pct Max (all)",    width: 100, numeric: true,  tooltip: "Max pct averaged across ALL tasks (0 for no value)." },
  { key: "sum_pct_avg",  label: "\u03A3 Pct Avg",   width: 90,  numeric: true,  tooltip: "Sum of per-task avg pct across all tasks with a value." },
  { key: "sum_pct_max",  label: "\u03A3 Pct Max",   width: 90,  numeric: true,  tooltip: "Sum of per-task max pct across all tasks with a value." },
  { key: "pct_affected", label: "% Tasks Aff.",     width: 100, numeric: true,  tooltip: "% Tasks Affected from the compute panel. Uses the selected datasets and method." },
  { key: "workers_aff",  label: "Workers Aff.",     width: 110, numeric: true,  tooltip: "Workers affected = % Tasks Affected \u00d7 employment. Requires compute panel result." },
  { key: "wages_aff",    label: "Wages Aff. ($B)",  width: 120, numeric: true,  tooltip: "Wages affected (billions) = % Tasks Affected \u00d7 employment \u00d7 median wage. Requires compute panel result." },
];

// ── FlatRow model ──────────────────────────────────────────────────────────────

interface FlatRow {
  name: string;
  rowId?: string;
  emp: number;
  wage: number | null;
  n_occs: number;
  n_tasks: number;
  auto_avg_with_vals: number | null;
  auto_max_with_vals: number | null;
  auto_avg_all: number | null;
  auto_max_all: number | null;
  pct_physical: number | null;
  pct_avg_with_vals: number | null;
  pct_max_with_vals: number | null;
  pct_avg_all: number | null;
  pct_max_all: number | null;
  sum_pct_avg: number | null;
  sum_pct_max: number | null;
  parent?: string | null;
  grandparent?: string | null;
  sourceOccs?: OccupationSummary[];
  isOcc?: boolean;
  // Task-level fields (only set when tableLevel === "task")
  title_current?: string | null;
  major_occ_category?: string | null;
  minor_occ_category?: string | null;
  broad_occ?: string | null;
  dwa_title?: string | null;
  iwa_title?: string | null;
  gwa_title?: string | null;
  physical?: boolean | null;
  freq_mean?: number | null;
  importance?: number | null;
  relevance?: number | null;
  sources?: Record<string, TaskSourceStats>;
  top_mcps?: McpEntry[];
}

// ── Row converters ─────────────────────────────────────────────────────────────

function groupToRow(g: ExplorerGroupRow, geo: "nat" | "ut"): FlatRow {
  return {
    name: g.name,
    emp: (geo === "nat" ? g.emp_nat : g.emp_ut) ?? 0,
    wage: (geo === "nat" ? g.wage_nat : g.wage_ut) ?? null,
    n_occs: g.n_occs,
    n_tasks: g.n_tasks,
    auto_avg_with_vals: g.auto_avg_with_vals ?? null,
    auto_max_with_vals: g.auto_max_with_vals ?? null,
    auto_avg_all: g.auto_avg_all ?? null,
    auto_max_all: g.auto_max_all ?? null,
    pct_physical: g.pct_physical ?? null,
    pct_avg_with_vals: g.pct_avg_with_vals ?? null,
    pct_max_with_vals: g.pct_max_with_vals ?? null,
    pct_avg_all: g.pct_avg_all ?? null,
    pct_max_all: g.pct_max_all ?? null,
    sum_pct_avg: g.sum_pct_avg ?? null,
    sum_pct_max: g.sum_pct_max ?? null,
    parent: g.parent ?? null,
    grandparent: g.grandparent ?? null,
  };
}

function occToRow(occ: OccupationSummary, geo: "nat" | "ut"): FlatRow {
  return {
    name: occ.title_current,
    emp: (geo === "nat" ? occ.emp_nat : occ.emp_ut) ?? 0,
    wage: (geo === "nat" ? occ.wage_nat : occ.wage_ut) ?? null,
    n_occs: 1,
    n_tasks: occ.n_tasks,
    auto_avg_with_vals: occ.auto_avg_with_vals ?? null,
    auto_max_with_vals: occ.auto_max_with_vals ?? null,
    auto_avg_all: occ.auto_avg_all ?? null,
    auto_max_all: occ.auto_max_all ?? null,
    pct_physical: occ.pct_physical ?? null,
    pct_avg_with_vals: occ.pct_avg_with_vals ?? null,
    pct_max_with_vals: occ.pct_max_with_vals ?? null,
    pct_avg_all: occ.pct_avg_all ?? null,
    pct_max_all: occ.pct_max_all ?? null,
    sum_pct_avg: occ.sum_pct_avg ?? null,
    sum_pct_max: occ.sum_pct_max ?? null,
    parent: occ.broad ?? null,
    grandparent: occ.minor ?? null,
    sourceOccs: [occ],
    isOcc: true,
  };
}

function ecoTaskToRow(t: EcoTaskRow, idx: number, geo: "nat" | "ut" = "nat"): FlatRow {
  return {
    name: t.task,
    rowId: `eco:${idx}`,
    emp: (geo === "nat" ? t.emp_nat : t.emp_ut) ?? 0,
    wage: (geo === "nat" ? t.wage_nat : t.wage_ut) ?? null,
    n_occs: 1,
    n_tasks: 1,
    auto_avg_with_vals: t.avg_auto_aug ?? null,
    auto_max_with_vals: t.max_auto_aug ?? null,
    auto_avg_all: null,
    auto_max_all: null,
    pct_physical: t.physical === true ? 1 : t.physical === false ? 0 : null,
    pct_avg_with_vals: t.avg_pct_norm ?? null,
    pct_max_with_vals: t.max_pct_norm ?? null,
    pct_avg_all: null,
    pct_max_all: null,
    sum_pct_avg: null,
    sum_pct_max: null,
    title_current: t.title_current,
    major_occ_category: t.major_occ_category ?? null,
    minor_occ_category: t.minor_occ_category ?? null,
    broad_occ: t.broad_occ ?? null,
    dwa_title: t.dwa_title ?? null,
    iwa_title: t.iwa_title ?? null,
    gwa_title: t.gwa_title ?? null,
    physical: t.physical ?? null,
    freq_mean: t.freq_mean ?? null,
    importance: t.importance ?? null,
    relevance: t.relevance ?? null,
    sources: t.sources,
    top_mcps: t.top_mcps ?? [],
  };
}

// ── Column value getter ────────────────────────────────────────────────────────

function getVal(row: FlatRow, col: string, pctMap: Map<string, number> | null): number | null {
  // For task-level rows, pct is looked up by occupation name
  const pctKey = row.title_current ?? row.name;
  switch (col) {
    case "emp":          return row.emp;
    case "wage":         return row.wage;
    case "phys_col":     return row.physical === true ? 1 : row.physical === false ? 0 : null;
    case "n_occs":       return row.n_occs;
    case "n_tasks":      return row.n_tasks;
    case "auto_avg_w":   return row.auto_avg_with_vals;
    case "auto_max_w":   return row.auto_max_with_vals;
    case "auto_avg_all": return row.auto_avg_all;
    case "auto_max_all": return row.auto_max_all;
    case "pct_phys":     return row.pct_physical;
    case "pct_avg_w":    return row.pct_avg_with_vals;
    case "pct_max_w":    return row.pct_max_with_vals;
    case "pct_avg_all":  return row.pct_avg_all;
    case "pct_max_all":  return row.pct_max_all;
    case "sum_pct_avg":  return row.sum_pct_avg;
    case "sum_pct_max":  return row.sum_pct_max;
    case "freq_col":     return row.freq_mean ?? null;
    case "imp_col":      return row.importance ?? null;
    case "rel_col":      return row.relevance ?? null;
    case "pct_affected": return pctMap?.get(pctKey) ?? null;
    case "workers_aff": {
      const pct = pctMap?.get(pctKey);
      return pct != null ? (pct / 100) * row.emp : null;
    }
    case "wages_aff": {
      const pct = pctMap?.get(pctKey);
      return (pct != null && row.wage != null) ? (pct / 100) * row.emp * row.wage / 1e9 : null;
    }
    default:             return null;
  }
}

// ── Cell renderer ──────────────────────────────────────────────────────────────

function renderCell(
  col: string,
  row: FlatRow,
  pctMap: Map<string, number> | null,
): React.ReactNode {
  const muted = { color: "var(--text-muted)" } as React.CSSProperties;
  // For task-level rows, pct lookup uses occupation name
  const pctKey = row.title_current ?? row.name;
  switch (col) {
    case "occ":          return row.title_current ?? <span style={muted}>—</span>;
    case "major_cat":    return row.major_occ_category ?? <span style={muted}>—</span>;
    case "minor_cat":    return row.minor_occ_category ?? <span style={muted}>—</span>;
    case "broad_cat":    return row.broad_occ ?? <span style={muted}>—</span>;
    case "dwa_col":      return row.dwa_title ?? <span style={muted}>—</span>;
    case "iwa_col":      return row.iwa_title ?? <span style={muted}>—</span>;
    case "gwa_col":      return row.gwa_title ?? <span style={muted}>—</span>;
    case "phys_col": {
      if (row.physical === true) return <span style={{ color: "#16a34a" }}>✓</span>;
      if (row.physical === false) return <span style={{ color: "var(--text-muted)" }}>✗</span>;
      return <span style={{ color: "var(--text-muted)" }}>—</span>;
    }
    case "emp":          return fmtEmp(row.emp);
    case "wage":         return fmtWage(row.wage);
    case "n_occs":       return row.isOcc ? <span style={muted}>—</span> : row.n_occs;
    case "n_tasks":      return row.n_tasks;
    case "auto_avg_w":   return <AutoCell v={row.auto_avg_with_vals} />;
    case "auto_max_w":   return <AutoCell v={row.auto_max_with_vals} />;
    case "auto_avg_all": return <AutoCell v={row.auto_avg_all} />;
    case "auto_max_all": return <AutoCell v={row.auto_max_all} />;
    case "pct_phys":     return fmtPctPhys(row.pct_physical);
    case "pct_avg_w":    return fmtPctNorm(row.pct_avg_with_vals);
    case "pct_max_w":    return fmtPctNorm(row.pct_max_with_vals);
    case "pct_avg_all":  return fmtPctNorm(row.pct_avg_all);
    case "pct_max_all":  return fmtPctNorm(row.pct_max_all);
    case "sum_pct_avg":  return fmtPctNorm(row.sum_pct_avg);
    case "sum_pct_max":  return fmtPctNorm(row.sum_pct_max);
    case "freq_col":     return row.freq_mean != null ? row.freq_mean.toFixed(1) : <span style={muted}>—</span>;
    case "imp_col":      return row.importance != null ? row.importance.toFixed(1) : <span style={muted}>—</span>;
    case "rel_col":      return row.relevance != null ? row.relevance.toFixed(0) : <span style={muted}>—</span>;
    case "pct_affected": {
      const v = pctMap?.get(pctKey) ?? null;
      return v != null
        ? <span style={{ color: "var(--brand)", fontWeight: 500 }}>{v.toFixed(2)}%</span>
        : <span style={muted}>—</span>;
    }
    case "workers_aff": {
      const pct = pctMap?.get(pctKey);
      if (pct == null) return <span style={muted}>—</span>;
      const v = (pct / 100) * row.emp;
      return <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtEmp(v)}</span>;
    }
    case "wages_aff": {
      const pct = pctMap?.get(pctKey);
      if (pct == null || row.wage == null) return <span style={muted}>—</span>;
      const rawDollars = (pct / 100) * row.emp * row.wage;
      const fmtWagesAff = rawDollars >= 1e9 ? `$${(rawDollars / 1e9).toFixed(2)}B`
        : rawDollars >= 1e6 ? `$${(rawDollars / 1e6).toFixed(2)}M`
        : rawDollars >= 1e3 ? `$${(rawDollars / 1e3).toFixed(0)}K`
        : `$${rawDollars.toFixed(0)}`;
      return <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtWagesAff}</span>;
    }
    default: return null;
  }
}

function AutoCell({ v }: { v: number | null | undefined }) {
  if (v == null) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  return (
    <span style={{ color: v > 0 ? "var(--brand)" : "var(--text-muted)" }}>
      {fmtAutoAug(v)}
    </span>
  );
}

// ── Text highlight helper ──────────────────────────────────────────────────────

function highlightText(text: string, query: string): React.ReactNode {
  if (!query) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <mark style={{ background: "#fef08a", borderRadius: 2 }}>{text.slice(idx, idx + query.length)}</mark>
      {text.slice(idx + query.length)}
    </>
  );
}

// ── Icons ──────────────────────────────────────────────────────────────────────

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: open ? "rotate(0deg)" : "rotate(-90deg)", transition: "transform 0.18s ease", flexShrink: 0, color: "var(--text-muted)" }}
      aria-hidden="true"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function FunnelIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  );
}

// ── Portal-based InfoTooltip ───────────────────────────────────────────────────

function InfoTooltip({ text }: { text: string }) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const TOOLTIP_W = 300;
  const TOOLTIP_H = 60;

  const clamp = (x: number, y: number) => {
    const safeX = typeof window !== "undefined" ? Math.min(x, window.innerWidth - TOOLTIP_W - 10) : x;
    const safeY = typeof window !== "undefined" && y + TOOLTIP_H > window.innerHeight ? y - TOOLTIP_H - 10 : y;
    return { x: safeX, y: safeY };
  };

  const handleMove = (e: React.MouseEvent) => {
    setPos(clamp(e.clientX + 12, e.clientY + 14));
  };

  return (
    <span style={{ position: "relative", display: "inline-flex", alignItems: "center", marginLeft: 3 }}>
      <span
        onMouseEnter={(e) => setPos(clamp(e.clientX + 12, e.clientY + 14))}
        onMouseMove={handleMove}
        onMouseLeave={() => setPos(null)}
        style={{
          cursor: "help", color: "var(--text-muted)", fontSize: 9, fontWeight: 700,
          border: "1px solid var(--border)", borderRadius: "50%",
          width: 12, height: 12, display: "inline-flex", alignItems: "center", justifyContent: "center",
          lineHeight: 1, userSelect: "none",
        }}
      >?</span>
      {pos && typeof document !== "undefined" && createPortal(
        <div style={{
          position: "fixed", left: pos.x, top: pos.y,
          background: "#1a1a1a", color: "#fff", fontSize: 11, padding: "6px 10px",
          borderRadius: 6, maxWidth: TOOLTIP_W, zIndex: 9999, pointerEvents: "none",
          boxShadow: "0 2px 8px rgba(0,0,0,0.25)", lineHeight: 1.45,
        }}>
          {text}
        </div>,
        document.body
      )}
    </span>
  );
}

// ── Column filter dropdown ─────────────────────────────────────────────────────

function ColumnFilterDropdown({
  colKey,
  filters,
  setFilters,
  onClose,
}: {
  colKey: string;
  filters: Record<string, { min: string; max: string }>;
  setFilters: React.Dispatch<React.SetStateAction<Record<string, { min: string; max: string }>>>;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const cur = filters[colKey] ?? { min: "", max: "" };

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const setMinMax = (field: "min" | "max", val: string) => {
    setFilters((prev) => ({ ...prev, [colKey]: { ...cur, [field]: val } }));
  };

  const hasFilter = cur.min !== "" || cur.max !== "";

  return (
    <div ref={ref} style={{
      position: "absolute", top: "100%", right: 0, zIndex: 500,
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 7, padding: "10px 12px", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      minWidth: 140, display: "flex", flexDirection: "column", gap: 7,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 10, color: "var(--text-muted)", width: 14 }}>&ge;</span>
        <input
          type="number"
          value={cur.min}
          onChange={(e) => setMinMax("min", e.target.value)}
          placeholder="min"
          style={{
            width: "100%", fontSize: 11, padding: "4px 6px",
            border: "1px solid var(--border)", borderRadius: 4,
            outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)",
          }}
        />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 10, color: "var(--text-muted)", width: 14 }}>&le;</span>
        <input
          type="number"
          value={cur.max}
          onChange={(e) => setMinMax("max", e.target.value)}
          placeholder="max"
          style={{
            width: "100%", fontSize: 11, padding: "4px 6px",
            border: "1px solid var(--border)", borderRadius: 4,
            outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)",
          }}
        />
      </div>
      {hasFilter && (
        <button
          onClick={() => setFilters((prev) => ({ ...prev, [colKey]: { min: "", max: "" } }))}
          style={{
            fontSize: 10, color: "var(--brand)", background: "none", border: "none",
            cursor: "pointer", padding: 0, textAlign: "left",
          }}
        >Clear</button>
      )}
    </div>
  );
}

// ── Text column filter dropdown ──────────────────────────────────────────────

const TEXT_FILTER_COLS = new Set(["occ", "broad_cat", "minor_cat", "major_cat", "dwa_col", "iwa_col", "gwa_col"]);

function TextColumnFilterDropdown({
  colKey,
  uniqueValues,
  selectedValues,
  onSelectionChange,
  onClose,
}: {
  colKey: string;
  uniqueValues: string[];
  selectedValues: Set<string> | null; // null means "all"
  onSelectionChange: (colKey: string, values: Set<string> | null) => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [filterSearch, setFilterSearch] = useState("");

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const isAll = selectedValues === null;
  const filtered = filterSearch
    ? uniqueValues.filter((v) => v.toLowerCase().includes(filterSearch.toLowerCase()))
    : uniqueValues;

  return (
    <div ref={ref} style={{
      position: "absolute", top: "100%", left: 0, zIndex: 500,
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 7, padding: "8px 0", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      minWidth: 220, maxWidth: 320, display: "flex", flexDirection: "column",
    }} onClick={(e) => e.stopPropagation()}>
      {/* Search box */}
      <div style={{ padding: "0 8px 6px" }}>
        <input
          type="text"
          placeholder="Search..."
          value={filterSearch}
          onChange={(e) => setFilterSearch(e.target.value)}
          style={{
            width: "100%", fontSize: 11, padding: "4px 6px",
            border: "1px solid var(--border)", borderRadius: 4,
            outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)",
            boxSizing: "border-box",
          }}
        />
      </div>
      {/* All toggle */}
      <label
        style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "3px 10px", fontSize: 11, cursor: "pointer",
          color: "var(--text-primary)", fontWeight: 600,
          borderBottom: "1px solid var(--border-light)",
        }}
      >
        <input
          type="checkbox"
          checked={isAll}
          onChange={() => {
            if (isAll) {
              // Deselect all — set empty
              onSelectionChange(colKey, new Set());
            } else {
              // Select all
              onSelectionChange(colKey, null);
            }
          }}
          style={{ margin: 0 }}
        />
        All ({uniqueValues.length})
      </label>
      {/* Values list */}
      <div style={{ maxHeight: 250, overflowY: "auto" }}>
        {filtered.map((val) => {
          const checked = isAll || (selectedValues?.has(val) ?? false);
          return (
            <label
              key={val}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "3px 10px", fontSize: 11, cursor: "pointer",
                color: checked ? "var(--text-primary)" : "var(--text-muted)",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "#f5f5f3"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => {
                  if (isAll) {
                    // Switching from "all" to specific: select all except this one
                    const next = new Set(uniqueValues);
                    next.delete(val);
                    onSelectionChange(colKey, next);
                  } else {
                    const next = new Set(selectedValues);
                    if (next.has(val)) next.delete(val); else next.add(val);
                    // If all are selected, switch back to null (all)
                    if (next.size === uniqueValues.length) {
                      onSelectionChange(colKey, null);
                    } else {
                      onSelectionChange(colKey, next);
                    }
                  }
                }}
                style={{ margin: 0 }}
              />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{val}</span>
            </label>
          );
        })}
        {filtered.length === 0 && (
          <p style={{ fontSize: 11, color: "var(--text-muted)", padding: "6px 10px", margin: 0 }}>No matches</p>
        )}
      </div>
      {/* Clear button */}
      {!isAll && (
        <div style={{ borderTop: "1px solid var(--border-light)", padding: "4px 10px 2px" }}>
          <button
            onClick={() => onSelectionChange(colKey, null)}
            style={{
              fontSize: 10, color: "var(--brand)", background: "none", border: "none",
              cursor: "pointer", padding: 0, textAlign: "left",
            }}
          >Reset to All</button>
        </div>
      )}
    </div>
  );
}

// ── Segmented button control ───────────────────────────────────────────────────

function BtnSeg<T extends string>({
  opts,
  val,
  onChange,
}: {
  opts: { v: T; l: string }[];
  val: T;
  onChange: (v: T) => void;
}) {
  return (
    <div style={{ display: "inline-flex", border: "1px solid var(--border)", borderRadius: 5, overflow: "hidden" }}>
      {opts.map(({ v, l }, i) => (
        <button key={v} onClick={() => onChange(v)} style={{
          padding: "3px 8px", fontSize: 11, cursor: "pointer", border: "none",
          borderRight: i < opts.length - 1 ? "1px solid var(--border)" : "none",
          background: val === v ? "var(--brand-light)" : "transparent",
          color: val === v ? "var(--brand)" : "var(--text-secondary)",
          fontWeight: val === v ? 600 : 400,
        }}>{l}</button>
      ))}
    </div>
  );
}

// ── Task detail sub-table ──────────────────────────────────────────────────────

function TaskSubRow({
  task,
  physicalMode,
  occHierarchy,
  emp,
  wage,
}: {
  task: TaskDetail;
  physicalMode: "all" | "exclude" | "only";
  occHierarchy?: { broad?: string | null; minor?: string | null; major?: string | null };
  emp?: number;
  wage?: number | null;
}) {
  const [expanded, setExpanded] = useState(false);

  if (physicalMode === "exclude" && task.physical === true) return null;
  if (physicalMode === "only" && task.physical !== true) return null;

  const avgAuto = task.avg_auto_aug;
  const maxAuto = task.max_auto_aug;
  const avgPct  = task.avg_pct_norm;
  const maxPct  = task.max_pct_norm;
  const barPct  = avgAuto != null ? Math.min(avgAuto / 5, 1) * 100 : null;

  const sources = Object.entries(task.sources ?? {});

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "6px 10px", fontSize: 12, color: "var(--text-primary)", verticalAlign: "top" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 5 }}>
            <ChevronIcon open={expanded} />
            <span style={{ lineHeight: 1.4 }}>{task.task}</span>
          </div>
        </td>
        <td style={{ padding: "6px 6px", textAlign: "center", verticalAlign: "top", width: 44 }}>
          {task.physical === true
            ? <span style={{ color: "#16a34a", fontSize: 12 }}>✓</span>
            : task.physical === false
            ? <span style={{ color: "var(--text-muted)", fontSize: 12 }}>✗</span>
            : <span style={{ color: "var(--text-muted)", fontSize: 11 }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", width: 48 }}>
          {task.freq_mean?.toFixed(1) ?? "—"}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", width: 48 }}>
          {task.importance?.toFixed(1) ?? "—"}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", width: 48 }}>
          {task.relevance?.toFixed(0) ?? "—"}
        </td>
        <td style={{ padding: "6px 6px", verticalAlign: "top", width: 100 }}>
          {barPct != null ? (
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <div style={{ width: 48, height: 5, background: "var(--border)", borderRadius: 3, overflow: "hidden", flexShrink: 0 }}>
                <div style={{ width: `${barPct}%`, height: "100%", background: "var(--brand)", borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{avgAuto?.toFixed(2)}</span>
            </div>
          ) : <span style={{ fontSize: 11, color: "var(--text-muted)" }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", width: 72, verticalAlign: "top" }}>
          {fmtAutoAug(maxAuto)}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 12, textAlign: "right", width: 80, verticalAlign: "top" }}>
          {avgPct != null
            ? <span style={{ color: "var(--brand)" }}>{fmtPctNorm(avgPct)}</span>
            : <span style={{ color: "var(--text-muted)" }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 12, textAlign: "right", width: 80, verticalAlign: "top" }}>
          {maxPct != null
            ? <span style={{ color: "var(--brand)" }}>{fmtPctNorm(maxPct)}</span>
            : <span style={{ color: "var(--text-muted)" }}>—</span>}
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#fafaf8", borderBottom: "1px solid var(--border-light)" }}>
          <td colSpan={9} style={{ padding: "10px 20px 14px 28px" }}>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              {occHierarchy && (occHierarchy.broad || occHierarchy.minor || occHierarchy.major) && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Occupation Categories</p>
                  {occHierarchy.broad && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Broad:</b> {occHierarchy.broad}</p>}
                  {occHierarchy.minor && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Minor:</b> {occHierarchy.minor}</p>}
                  {occHierarchy.major && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>Major:</b> {occHierarchy.major}</p>}
                </div>
              )}
              {(task.gwa_title || task.iwa_title || task.dwa_title) && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Work Activities</p>
                  {task.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {task.gwa_title}</p>}
                  {task.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {task.iwa_title}</p>}
                  {task.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {task.dwa_title}</p>}
                </div>
              )}
              {/* Task Detail side table */}
              <div style={{ minWidth: 140 }}>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Task Detail</p>
                <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                  <tbody>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Emp</td>
                      <td style={{ padding: "2px 0" }}>{fmtEmp(emp)}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Wage</td>
                      <td style={{ padding: "2px 0" }}>{fmtWage(wage)}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Physical</td>
                      <td style={{ padding: "2px 0" }}>
                        {task.physical === true
                          ? <span style={{ color: "#16a34a" }}>Yes</span>
                          : task.physical === false
                          ? <span style={{ color: "var(--text-secondary)" }}>No</span>
                          : <span style={{ color: "var(--text-muted)" }}>—</span>}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Freq</td>
                      <td style={{ padding: "2px 0" }}>{task.freq_mean?.toFixed(2) ?? "—"}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Imp</td>
                      <td style={{ padding: "2px 0" }}>{task.importance?.toFixed(2) ?? "—"}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Rel</td>
                      <td style={{ padding: "2px 0" }}>{task.relevance?.toFixed(0) ?? "—"}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              {sources.length > 0 && (
                <div>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Source Breakdown</p>
                  <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                    <thead>
                      <tr>
                        <th style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "left" }}>Source</th>
                        <th style={{ padding: "2px 8px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Auto-aug</th>
                        <th style={{ padding: "2px 8px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Pct</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sources.map(([src, stats]) => (
                        <tr key={src}>
                          <td style={{ padding: "2px 10px 2px 0" }}>
                            <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--bg-sidebar)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}>{src}</span>
                          </td>
                          <td style={{ padding: "2px 8px", textAlign: "right" }}>
                            {stats.auto_aug != null ? stats.auto_aug.toFixed(3) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                          </td>
                          <td style={{ padding: "2px 8px", textAlign: "right" }}>
                            {stats.pct_norm != null ? fmtPctNorm(stats.pct_norm) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                          </td>
                        </tr>
                      ))}
                      <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                        <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                          <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--brand-light)", border: "1px solid var(--brand)", color: "var(--brand)", fontWeight: 700 }}>AVG</span>
                        </td>
                        <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>
                          {avgAuto != null ? avgAuto.toFixed(3) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                        </td>
                        <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>
                          {avgPct != null ? fmtPctNorm(avgPct) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 4px 0", fontWeight: 700 }}>
                          <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "#fffbeb", border: "1px solid #d97706", color: "#d97706", fontWeight: 700 }}>MAX</span>
                        </td>
                        <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>
                          {maxAuto != null ? maxAuto.toFixed(3) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                        </td>
                        <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>
                          {maxPct != null ? fmtPctNorm(maxPct) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
              {/* Top MCPs */}
              {task.top_mcps && task.top_mcps.length > 0 && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Top MCP Servers</p>
                  <ul style={{ margin: 0, paddingLeft: 16, listStyleType: "disc" }}>
                    {task.top_mcps.slice(0, 5).map((mcp, mi) => (
                      <li key={mi} style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 3 }}>
                        {mcp.url
                          ? <a href={mcp.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand)", textDecoration: "underline" }}>{mcp.title}</a>
                          : mcp.title}
                        {mcp.rating != null && (
                          <span style={{ marginLeft: 6, fontSize: 10, color: "var(--text-muted)" }}>({mcp.rating.toFixed(2)})</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// Task sub-table header
function TaskSubHeader() {
  return (
    <tr style={{ borderBottom: "2px solid var(--border)" }}>
      <th style={{ padding: "5px 10px 5px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Task</th>
      <th style={{ padding: "5px 6px", textAlign: "center", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 44 }}>Phys</th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 48, whiteSpace: "nowrap" }}>
        Freq<InfoTooltip text="O*NET frequency (0–10)" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 48, whiteSpace: "nowrap" }}>
        Imp<InfoTooltip text="O*NET importance (0–5)" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 48, whiteSpace: "nowrap" }}>
        Rel<InfoTooltip text="O*NET relevance (0–100)" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 100, whiteSpace: "nowrap" }}>
        Auto Avg<InfoTooltip text="Avg auto-aug (0–5) across sources" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 72, whiteSpace: "nowrap" }}>
        Auto Max
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Pct Avg<InfoTooltip text="Avg pct (share of AI conversations)" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Pct Max
      </th>
    </tr>
  );
}

// ── % Tasks Affected compute panel ─────────────────────────────────────────────

interface PctSettings {
  datasets: string[];
  combineMethod: "Average" | "Max";
  method: "freq" | "imp";
  geo: "nat" | "ut";
  physicalMode: "all" | "exclude" | "only";
  useAutoAug: boolean;
}

function PctComputePanel({
  config,
  geo,
  tableLevel,
  onResult,
}: {
  config: ConfigResponse;
  geo: "nat" | "ut";
  tableLevel: TableLevel;
  onResult: (map: Map<string, number> | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState<PctSettings>({
    datasets: ["AEI v4"],
    combineMethod: "Average",
    method: "freq",
    geo,
    physicalMode: "all",
    useAutoAug: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [computed, setComputed] = useState(false);

  const geoChangedRef = useRef(false);
  useEffect(() => {
    setSettings((s) => {
      if (s.geo !== geo) geoChangedRef.current = true;
      return { ...s, geo };
    });
  }, [geo]);

  function set<K extends keyof PctSettings>(k: K, v: PctSettings[K]) {
    setSettings((s) => ({ ...s, [k]: v }));
  }

  // Map task/occupation level → "occupation" for backend; task level treated as occupation
  const backendAggLevel = (tableLevel === "task" || tableLevel === "occupation") ? "occupation"
    : tableLevel as "major" | "minor" | "broad";

  const compute = useCallback(async () => {
    if (!settings.datasets.length) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchCompute({
        selectedDatasets: settings.datasets,
        combineMethod: settings.combineMethod,
        method: settings.method,
        useAutoAug: settings.useAutoAug,
        physicalMode: settings.physicalMode,
        geo: settings.geo,
        aggLevel: backendAggLevel,
        sortBy: "Workers Affected",
        topN: 5000,
        searchQuery: "",
        contextSize: 5,
      });
      const map = new Map<string, number>();
      resp.rows.forEach((r: ChartRow) => map.set(r.category, r.pct_tasks_affected));
      onResult(map);
      setComputed(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Compute failed");
    } finally {
      setLoading(false);
    }
  }, [settings, onResult, backendAggLevel]);

  // Auto-recompute when geo changes while already computed
  useEffect(() => {
    if (geoChangedRef.current && computed && !loading) {
      geoChangedRef.current = false;
      compute();
    }
  }, [settings.geo, computed, loading, compute]);

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 8,
          padding: "8px 14px", background: open ? "var(--brand-light)" : "var(--bg-surface)",
          border: "none", cursor: "pointer", textAlign: "left",
        }}
      >
        <ChevronIcon open={open} />
        <span style={{ fontSize: 11, fontWeight: 600, color: open ? "var(--brand)" : "var(--text-secondary)" }}>
          % Tasks Affected {computed ? "✓" : "(configure & compute)"}
        </span>
        {computed && (
          <button
            onClick={(e) => { e.stopPropagation(); onResult(null); setComputed(false); }}
            style={{ marginLeft: "auto", fontSize: 10, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}
          >Clear</button>
        )}
      </button>
      {open && (
        <div style={{ padding: "12px 14px", borderTop: "1px solid var(--border)", background: "var(--bg-surface)", display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
            <div>
              <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Datasets</p>
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap", maxWidth: 420 }}>
                {config.datasets.map((ds) => {
                  const avail = config.dataset_availability[ds];
                  const sel = settings.datasets.includes(ds);
                  return (
                    <button key={ds} disabled={!avail} onClick={() => {
                      const next = enforceDatasetToggle(settings.datasets, ds, {
                        aeiSnapshotDatasets: config.aei_snapshot_datasets ?? [],
                        aeiCumulativeDatasets: config.aei_cumulative_datasets ?? [],
                        mcpDatasets: config.mcp_datasets ?? [],
                      });
                      set("datasets", next);
                    }} style={{
                      fontSize: 10, padding: "3px 7px", borderRadius: 5,
                      border: `1.5px solid ${sel ? "var(--brand)" : "var(--border)"}`,
                      background: sel ? "var(--brand-light)" : "transparent",
                      color: sel ? "var(--brand)" : avail ? "var(--text-secondary)" : "var(--text-muted)",
                      cursor: avail ? "pointer" : "default",
                      fontWeight: sel ? 600 : 400,
                      textDecoration: avail ? "none" : "line-through",
                    }}>{ds}</button>
                  );
                })}
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
              {settings.datasets.length > 1 && (
                <div>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Combine</p>
                  <BtnSeg opts={[{ v: "Average", l: "Avg" }, { v: "Max", l: "Max" }]} val={settings.combineMethod} onChange={(v) => set("combineMethod", v)} />
                </div>
              )}
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Method</p>
                <BtnSeg opts={[{ v: "freq", l: "Time" }, { v: "imp", l: "Value" }]} val={settings.method} onChange={(v) => set("method", v)} />
              </div>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Physical</p>
                <BtnSeg opts={[{ v: "all", l: "All" }, { v: "exclude", l: "No Phys" }, { v: "only", l: "Phys only" }]} val={settings.physicalMode} onChange={(v) => set("physicalMode", v)} />
              </div>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Auto-aug</p>
                <BtnSeg opts={[{ v: "false", l: "Off" }, { v: "true", l: "On" }]} val={String(settings.useAutoAug)} onChange={(v) => set("useAutoAug", v === "true")} />
              </div>
              <button
                onClick={compute}
                disabled={loading || !settings.datasets.length}
                className="btn-brand"
                style={{ padding: "6px 18px", fontSize: 12, opacity: loading || !settings.datasets.length ? 0.5 : 1 }}
              >
                {loading ? "Computing…" : "Compute %"}
              </button>
            </div>
          </div>
          {error && <p style={{ fontSize: 11, color: "#b91c1c", margin: 0 }}>Error: {error}</p>}
          {computed && <p style={{ fontSize: 11, color: "#16a34a", margin: 0 }}>Computed — use the slider to filter rows.</p>}
        </div>
      )}
    </div>
  );
}

// ── Table types ────────────────────────────────────────────────────────────────

type TableLevel = "major" | "minor" | "broad" | "occupation" | "task";
type SortDir = "asc" | "desc";

const LEVEL_OPTIONS: { v: TableLevel; l: string }[] = [
  { v: "major", l: "Major" },
  { v: "minor", l: "Minor" },
  { v: "broad", l: "Broad" },
  { v: "occupation", l: "Occupation" },
  { v: "task", l: "Task" },
];

// ── Main ExplorerView ──────────────────────────────────────────────────────────

// Columns visible in simple mode
const SIMPLE_COLS = new Set([
  "name", "emp", "wage", "n_occs", "n_tasks",
  "auto_avg_all",
  "pct_avg_all", "sum_pct_avg",
  "pct_affected", "workers_aff", "wages_aff",
]);

// Columns visible in simple mode at task level (replaces SIMPLE_COLS for task view)
const SIMPLE_TASK_COLS = new Set([
  "name", "occ", "major_cat", "gwa_col",
  "emp", "wage",
  "auto_avg_w", "pct_avg_w",
  "pct_affected", "workers_aff", "wages_aff",
]);

// Label overrides for simple task mode
const SIMPLE_TASK_LABELS: Record<string, string> = {
  auto_avg_w: "Auto Avg",
  auto_max_w: "Auto Max",
  pct_avg_w: "Pct Avg",
  pct_max_w: "Pct Max",
};

export default function ExplorerView({ occupations, groups, config }: Props) {
  const { isSimple } = useSimpleMode();

  // ── State ──────────────────────────────────────────────────────────────────
  const [tableLevel, setTableLevel] = useState<TableLevel>("major");
  const [selectedMajors, setSelectedMajors] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [searchLevel, setSearchLevel] = useState<"all" | "major" | "minor" | "broad" | "occ" | "task">("all");
  const [sortCol, setSortCol] = useState<string>("emp");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [colFilters, setColFilters] = useState<Record<string, { min: string; max: string }>>({});
  const [openFilter, setOpenFilter] = useState<string | null>(null);
  const [geo, setGeo] = useState<"nat" | "ut">("nat");
  const [physicalMode, setPhysicalMode] = useState<"all" | "exclude" | "only">("all");
  const [pctAffectedMap, setPctAffectedMap] = useState<Map<string, number> | null>(null);
  const [minPctAffected, setMinPctAffected] = useState(0);
  const [taskData, setTaskData] = useState<EcoTaskRow[] | null>(null);
  const [taskLoading, setTaskLoading] = useState(false);
  const [rowLimit, setRowLimit] = useState(100);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [rowTasks, setRowTasks] = useState<Record<string, TaskDetail[] | "loading" | "error">>({});
  const [textColFilters, setTextColFilters] = useState<Record<string, Set<string> | null>>({});
  const [openTextFilter, setOpenTextFilter] = useState<string | null>(null);

  // ── Debounced inputs (prevents topRows recompute on every keystroke) ──────
  const debouncedSearch   = useDebounce(search,   250);

  // ── Column selector state (persisted to localStorage) ──────────────────
  const TASK_ONLY_COLS = new Set(["occ", "major_cat", "minor_cat", "broad_cat", "dwa_col", "iwa_col", "gwa_col", "phys_col", "freq_col", "imp_col", "rel_col"]);
  const NON_TASK_COLS = new Set(["n_occs", "n_tasks", "auto_avg_all", "auto_max_all", "pct_phys", "pct_avg_all", "pct_max_all", "sum_pct_avg", "sum_pct_max"]);
  const [hiddenCols, setHiddenCols] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set<string>();
    try {
      const saved = localStorage.getItem("aea_explorer_hidden_cols");
      return saved ? new Set(JSON.parse(saved) as string[]) : new Set<string>();
    } catch { return new Set<string>(); }
  });
  const [colSelectorOpen, setColSelectorOpen] = useState(false);
  const colSelectorRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!colSelectorOpen) return;
    function handleClickOutside(e: MouseEvent) {
      if (colSelectorRef.current && !colSelectorRef.current.contains(e.target as Node)) {
        setColSelectorOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [colSelectorOpen]);
  useEffect(() => {
    try { localStorage.setItem("aea_explorer_hidden_cols", JSON.stringify(Array.from(hiddenCols))); } catch { /* silent */ }
  }, [hiddenCols]);

  // ── Load task data when task level selected ──────────────────────────────
  useEffect(() => {
    if (tableLevel === "task" && taskData === null && !taskLoading) {
      setTaskLoading(true);
      fetchAllEcoTasks()
        .then((res: { tasks: EcoTaskRow[] }) => setTaskData(res.tasks))
        .catch(() => setTaskData([]))
        .finally(() => setTaskLoading(false));
    }
  }, [tableLevel, taskData, taskLoading]);

  // ── Auto-compute pct with preset settings (runs on load for both modes) ──
  const [computeVersion, setComputeVersion] = useState(0);
  useEffect(() => {
    const availableDatasets = config.datasets.filter((d) => config.dataset_availability[d]);
    if (availableDatasets.length === 0) return;
    const backendAgg = (tableLevel === "task" || tableLevel === "occupation") ? "occupation"
      : tableLevel as "major" | "minor" | "broad";
    let cancelled = false;
    fetchCompute({
      selectedDatasets: availableDatasets,
      combineMethod: "Average",
      method: "freq",
      useAutoAug: true,
      physicalMode: "all",
      geo,
      aggLevel: backendAgg,
      sortBy: "Workers Affected",
      topN: 5000,
      searchQuery: "",
      contextSize: 5,
    }).then((resp) => {
      if (cancelled) return;
      const map = new Map<string, number>();
      resp.rows.forEach((r: ChartRow) => map.set(r.category, r.pct_tasks_affected));
      setPctAffectedMap(map);
    }).catch(() => { /* silent */ });
    return () => { cancelled = true; };
  }, [geo, tableLevel, config.datasets, config.dataset_availability, computeVersion]);

  // ── Reset row limit whenever the visible set changes ─────────────────────
  useEffect(() => { setRowLimit(100); }, [tableLevel, selectedMajors, debouncedSearch, searchLevel, colFilters, textColFilters, physicalMode, pctAffectedMap, minPctAffected, sortCol, sortDir]);

  // ── Derived: major pills ─────────────────────────────────────────────────
  const allMajors = useMemo(() => {
    const s = new Set(occupations.map((o) => o.major ?? "Unknown"));
    return Array.from(s).sort();
  }, [occupations]);

  const majorCounts = useMemo(() => {
    const m = new Map<string, number>();
    occupations.forEach((o) => {
      const k = o.major ?? "Unknown";
      m.set(k, (m.get(k) ?? 0) + 1);
    });
    return m;
  }, [occupations]);

  // ── Build top-level rows ─────────────────────────────────────────────────
  const topRows = useMemo<FlatRow[]>(() => {
    const searchQ = debouncedSearch.trim().toLowerCase();

    // Effective search level
    const effectiveLevel = searchLevel === "all" ? tableLevel : (
      searchLevel === "major" ? "major"
      : searchLevel === "minor" ? "minor"
      : searchLevel === "broad" ? "broad"
      : searchLevel === "occ" ? "occupation"
      : "task"
    );

    let rows: FlatRow[] = [];

    if (tableLevel === "task") {
      let data = taskData ?? [];
      // Filter by major pills
      if (selectedMajors.size > 0) {
        data = data.filter((t) => t.major_occ_category != null && selectedMajors.has(t.major_occ_category));
      }
      rows = data.map((t, i) => ecoTaskToRow(t, i, geo));
    } else if (tableLevel === "occupation") {
      let occs = occupations;
      if (selectedMajors.size > 0) {
        occs = occs.filter((o) => selectedMajors.has(o.major ?? "Unknown"));
      }
      rows = occs.map((o) => occToRow(o, geo));
    } else {
      // major / minor / broad
      const srcRows: ExplorerGroupRow[] = groups[tableLevel as "major" | "minor" | "broad"] ?? [];
      rows = srcRows.map((g) => groupToRow(g, geo));
      if (selectedMajors.size > 0) {
        if (tableLevel === "major") {
          rows = rows.filter((r) => selectedMajors.has(r.name));
        } else if (tableLevel === "minor") {
          rows = rows.filter((r) => selectedMajors.has(r.parent ?? ""));
        } else if (tableLevel === "broad") {
          rows = rows.filter((r) => selectedMajors.has(r.grandparent ?? ""));
        }
      }
    }

    // Physical filter
    if (physicalMode === "exclude") {
      rows = rows.filter((r) => r.pct_physical !== 1);
    } else if (physicalMode === "only") {
      rows = rows.filter((r) => r.pct_physical === 1 || r.pct_physical === null);
    }

    // % Tasks Affected filter
    if (pctAffectedMap && minPctAffected > 0) {
      rows = rows.filter((r) => {
        const v = pctAffectedMap.get(r.name);
        return v != null && v >= minPctAffected;
      });
    }

    // Column filters
    Object.entries(colFilters).forEach(([key, { min, max }]) => {
      const minN = min !== "" ? parseFloat(min) : null;
      const maxN = max !== "" ? parseFloat(max) : null;
      if (minN !== null || maxN !== null) {
        rows = rows.filter((r) => {
          const v = getVal(r, key, pctAffectedMap);
          if (minN !== null && (v == null || v < minN)) return false;
          if (maxN !== null && (v == null || v > maxN)) return false;
          return true;
        });
      }
    });

    // Text column filters
    const textValGetter: Record<string, (r: FlatRow) => string | null | undefined> = {
      occ: (r) => r.title_current,
      major_cat: (r) => r.major_occ_category,
      minor_cat: (r) => r.minor_occ_category,
      broad_cat: (r) => r.broad_occ,
      dwa_col: (r) => r.dwa_title,
      iwa_col: (r) => r.iwa_title,
      gwa_col: (r) => r.gwa_title,
    };
    for (const [colKey, selected] of Object.entries(textColFilters)) {
      if (selected === null || selected === undefined) continue; // null means "all"
      if (selected.size === 0) { rows = []; break; }
      const getter = textValGetter[colKey];
      if (getter) {
        rows = rows.filter((r) => {
          const v = getter(r);
          return v != null && selected.has(v);
        });
      }
    }

    // Search
    if (searchQ) {
      if (effectiveLevel === tableLevel || searchLevel === "all") {
        rows = rows.filter((r) => {
          if (r.name.toLowerCase().includes(searchQ)) return true;
          // At task level also search occupation, major, minor, broad
          if (r.title_current?.toLowerCase().includes(searchQ)) return true;
          if (r.major_occ_category?.toLowerCase().includes(searchQ)) return true;
          if (r.minor_occ_category?.toLowerCase().includes(searchQ)) return true;
          if (r.broad_occ?.toLowerCase().includes(searchQ)) return true;
          return false;
        });
      }
    }

    // Sort
    rows = [...rows].sort((a, b) => {
      // Text column sorts
      const textColMap: Record<string, (r: FlatRow) => string | null | undefined> = {
        name: (r) => r.name,
        occ: (r) => r.title_current,
        major_cat: (r) => r.major_occ_category,
        minor_cat: (r) => r.minor_occ_category,
        broad_cat: (r) => r.broad_occ,
        dwa_col: (r) => r.dwa_title,
        iwa_col: (r) => r.iwa_title,
        gwa_col: (r) => r.gwa_title,
      };
      if (textColMap[sortCol]) {
        const aStr = textColMap[sortCol](a) ?? "";
        const bStr = textColMap[sortCol](b) ?? "";
        const cmp = aStr.localeCompare(bStr);
        return sortDir === "asc" ? cmp : -cmp;
      }
      const av = getVal(a, sortCol, pctAffectedMap);
      const bv = getVal(b, sortCol, pctAffectedMap);
      if (av == null && bv == null) return 0;
      if (av == null) return sortDir === "desc" ? 1 : -1;
      if (bv == null) return sortDir === "desc" ? -1 : 1;
      return sortDir === "desc" ? bv - av : av - bv;
    });

    return rows;
  }, [
    tableLevel, groups, occupations, taskData, geo, selectedMajors, debouncedSearch, searchLevel,
    sortCol, sortDir, colFilters, textColFilters, physicalMode, pctAffectedMap, minPctAffected,
  ]);

  // ── Expand/collapse ──────────────────────────────────────────────────────
  const toggleRow = useCallback((key: string, isOcc: boolean, name: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
        if (isOcc && !rowTasks[name]) {
          setRowTasks((rt) => ({ ...rt, [name]: "loading" }));
          fetchOccupationTasks(name)
            .then((data: OccupationTasksResponse) => setRowTasks((rt) => ({ ...rt, [name]: data.tasks })))
            .catch(() => setRowTasks((rt) => ({ ...rt, [name]: "error" })));
        }
      }
      return next;
    });
  }, [rowTasks]);

  // ── Column sort ──────────────────────────────────────────────────────────
  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir((d) => d === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortDir("desc");
    }
  };

  // ── Reset ────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setTableLevel("major");
    setSelectedMajors(new Set());
    setSearch("");
    setSearchLevel("all");
    setSortCol("emp");
    setSortDir("desc");
    setColFilters({});
    setTextColFilters({});
    setExpandedRows(new Set());
    setGeo("nat");
    setPhysicalMode("all");
    setHiddenCols(new Set());
    setMinPctAffected(0);
    setRowLimit(100);
    // Re-run auto-compute with default settings
    setPctAffectedMap(null);
    setComputeVersion((v) => v + 1);
  };

  // ── Visible columns (simple mode filters; column selector) ──
  const isSimpleTask = isSimple && tableLevel === "task";
  const visibleCols = useMemo(() => {
    return COLUMNS.filter((c) => {
      // pct_affected, workers_aff, wages_aff are always visible (show "—" when no data)
      // Simple mode column filter (task level uses different set)
      if (isSimpleTask && !SIMPLE_TASK_COLS.has(c.key)) return false;
      if (isSimple && !isSimpleTask && !SIMPLE_COLS.has(c.key)) return false;
      // Task-only columns hidden when not at task level
      if (TASK_ONLY_COLS.has(c.key) && tableLevel !== "task") return false;
      if (NON_TASK_COLS.has(c.key) && tableLevel === "task") return false;
      // User column selector
      if (hiddenCols.has(c.key)) return false;
      return true;
    }).map((c) => {
      // Relabel columns at task level
      if (tableLevel === "task" && SIMPLE_TASK_LABELS[c.key]) {
        return { ...c, label: SIMPLE_TASK_LABELS[c.key] };
      }
      return c;
    });
  }, [isSimple, isSimpleTask, tableLevel, hiddenCols]);

  // ── Total count for header ────────────────────────────────────────────────
  const totalOccs = occupations.length;
  const totalTasks = taskData?.length ?? null;

  // ── Unique values for text column filter dropdowns ─────────────────────
  const textColUniqueValues = useMemo(() => {
    const getters: Record<string, (r: FlatRow) => string | null | undefined> = {
      occ:       (r) => r.title_current,
      major_cat: (r) => r.major_occ_category,
      minor_cat: (r) => r.minor_occ_category,
      broad_cat: (r) => r.broad_occ,
      dwa_col:   (r) => r.dwa_title,
      iwa_col:   (r) => r.iwa_title,
      gwa_col:   (r) => r.gwa_title,
    };
    const result: Record<string, string[]> = {};
    for (const [key, getter] of Object.entries(getters)) {
      const seen = new Set<string>();
      topRows.forEach((r) => { const v = getter(r); if (v) seen.add(v); });
      result[key] = Array.from(seen).sort();
    }
    return result;
  }, [topRows]);

  // ── Pre-built child row cache (avoids O(n) filtering on every render) ─────
  const childRowCache = useMemo(() => {
    const cache = new Map<string, FlatRow[]>();
    (groups.major ?? []).forEach((g) => {
      cache.set(`major:${g.name}`, (groups.minor ?? [])
        .filter((m) => m.parent === g.name)
        .map((m) => groupToRow(m, geo))
        .sort((a, b) => b.emp - a.emp));
    });
    (groups.minor ?? []).forEach((g) => {
      cache.set(`minor:${g.name}`, (groups.broad ?? [])
        .filter((b) => b.parent === g.name)
        .map((b) => groupToRow(b, geo))
        .sort((a, b) => b.emp - a.emp));
    });
    (groups.broad ?? []).forEach((g) => {
      cache.set(`broad:${g.name}`, occupations
        .filter((o) => o.broad === g.name)
        .map((o) => occToRow(o, geo))
        .sort((a, b) => b.emp - a.emp));
    });
    return cache;
  }, [groups, occupations, geo]);

  // ── Build child rows for drilldown ────────────────────────────────────────
  function buildChildRows(row: FlatRow, currentLevel: TableLevel): FlatRow[] {
    if (currentLevel === "task" || currentLevel === "occupation") return [];
    return childRowCache.get(`${currentLevel}:${row.name}`) ?? [];
  }

  function childLevel(level: TableLevel): TableLevel {
    if (level === "major") return "minor";
    if (level === "minor") return "broad";
    if (level === "broad") return "occupation";
    return "task";
  }

  // ── Render a single table row (recursive) ────────────────────────────────
  function renderRow(row: FlatRow, level: TableLevel, indent: number): React.ReactNode {
    const rowKey = row.rowId ? `${level}:${row.rowId}` : `${level}:${row.name}`;
    const isExpanded = expandedRows.has(rowKey);
    const isOcc = level === "occupation" || row.isOcc === true;
    const isTask = level === "task";
    const indentPx = indent * 20;

    const taskState = isOcc ? rowTasks[row.name] : undefined;

    const childRowsData = (isExpanded && !isOcc && !isTask)
      ? buildChildRows(row, level)
      : [];
    const nextLvl = childLevel(level);

    return (
      <React.Fragment key={rowKey}>
        <tr
          onClick={() => toggleRow(rowKey, isOcc, row.name)}
          style={{
            cursor: "pointer",
            borderBottom: "1px solid var(--border-light)",
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = "#f9f9f7"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
        >
          {visibleCols.map((col, ci) => {
            const isName = col.key === "name";
            const isTextCol = !col.numeric;
            const isNum = col.numeric;
            return (
              <td
                key={col.key}
                style={{
                  padding: "7px 8px",
                  paddingLeft: isName ? 8 + indentPx : 8,
                  fontSize: 13,
                  color: "var(--text-primary)",
                  textAlign: isTextCol ? "left" : "right",
                  whiteSpace: isName ? "normal" : "nowrap",
                  verticalAlign: "top",
                  minWidth: ci === 0 ? col.width + indentPx : undefined,
                  width: ci === 0 ? undefined : col.width,
                  fontWeight: indent === 0 ? 500 : 400,
                }}
              >
                {isName ? (
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 5 }}>
                    <span style={{ marginTop: 1, flexShrink: 0 }}><ChevronIcon open={isExpanded} /></span>
                    <span style={{
                      lineHeight: 1.4,
                      ...(isTask ? {
                        display: "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical" as const,
                        overflow: "hidden",
                        wordBreak: "break-word" as const,
                      } : {}),
                    }}>
                      {search.trim() ? highlightText(row.name, search.trim()) : row.name}
                    </span>
                  </div>
                ) : isTextCol ? (
                  <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                    {renderCell(col.key, row, pctAffectedMap)}
                  </span>
                ) : (
                  <span style={{ color: isNum && getVal(row, col.key, pctAffectedMap) == null ? "var(--text-muted)" : undefined }}>
                    {renderCell(col.key, row, pctAffectedMap)}
                  </span>
                )}
              </td>
            );
          })}
        </tr>

        {/* Task sub-table for occupation */}
        {isExpanded && isOcc && (
          <tr style={{ background: "#f7f7f5", borderBottom: "1px solid var(--border)" }}>
            <td colSpan={visibleCols.length} style={{ padding: "0 0 6px", paddingLeft: indentPx + 28 }}>
              {taskState === "loading" && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 0" }}>
                  <div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading tasks…</span>
                </div>
              )}
              {taskState === "error" && (
                <p style={{ fontSize: 12, color: "#b91c1c", padding: "8px 0" }}>Failed to load tasks.</p>
              )}
              {Array.isArray(taskState) && taskState.length > 0 && (
                <div style={{ overflowX: "auto", marginTop: 8, marginRight: 8 }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                    <thead><TaskSubHeader /></thead>
                    <tbody>
                      {taskState.map((t) => (
                        <TaskSubRow
                          key={t.task_normalized}
                          task={t}
                          physicalMode={physicalMode}
                          occHierarchy={{
                            broad: row.parent ?? null,
                            minor: row.grandparent ?? null,
                            major: row.sourceOccs?.[0]?.major ?? null,
                          }}
                          emp={row.emp}
                          wage={row.wage}
                        />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {Array.isArray(taskState) && taskState.length === 0 && (
                <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "8px 0" }}>No tasks found.</p>
              )}
            </td>
          </tr>
        )}

        {/* Task-level expansion: show occupation + activity classification + details + sources + top MCPs */}
        {isExpanded && isTask && (
          <tr style={{ background: "#f7f7f5", borderBottom: "1px solid var(--border)" }}>
            <td colSpan={visibleCols.length} style={{ padding: "10px 20px 14px 28px" }}>
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                {/* Occupation Categories */}
                {(row.title_current || row.broad_occ || row.minor_occ_category || row.major_occ_category) && (
                  <div style={{ minWidth: 200 }}>
                    <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Occupation Categories</p>
                    {row.title_current && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Occupation:</b> {row.title_current}</p>}
                    {row.broad_occ && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Broad:</b> {row.broad_occ}</p>}
                    {row.minor_occ_category && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Minor:</b> {row.minor_occ_category}</p>}
                    {row.major_occ_category && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>Major:</b> {row.major_occ_category}</p>}
                  </div>
                )}
                {/* Work Activities */}
                {(row.gwa_title || row.iwa_title || row.dwa_title) && (
                  <div style={{ minWidth: 200 }}>
                    <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Work Activities</p>
                    {row.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {row.gwa_title}</p>}
                    {row.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {row.iwa_title}</p>}
                    {row.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {row.dwa_title}</p>}
                  </div>
                )}
                {/* Task Detail */}
                <div style={{ minWidth: 140 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Task Detail</p>
                  <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                    <tbody>
                      <tr>
                        <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Emp</td>
                        <td style={{ padding: "2px 0" }}>{fmtEmp(row.emp)}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Wage</td>
                        <td style={{ padding: "2px 0" }}>{fmtWage(row.wage)}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Physical</td>
                        <td style={{ padding: "2px 0" }}>
                          {row.pct_physical === 1
                            ? <span style={{ color: "#16a34a" }}>Yes</span>
                            : row.pct_physical === 0
                            ? <span style={{ color: "var(--text-secondary)" }}>No</span>
                            : <span style={{ color: "var(--text-muted)" }}>—</span>}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Freq</td>
                        <td style={{ padding: "2px 0" }}>{row.freq_mean?.toFixed(2) ?? "—"}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Imp</td>
                        <td style={{ padding: "2px 0" }}>{row.importance?.toFixed(2) ?? "—"}</td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Rel</td>
                        <td style={{ padding: "2px 0" }}>{row.relevance?.toFixed(0) ?? "—"}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                {/* Source Breakdown */}
                {row.sources && Object.keys(row.sources).length > 0 && (() => {
                  const sources = Object.entries(row.sources);
                  const autoVals = sources.map(([, s]) => s.auto_aug).filter((v): v is number => v != null);
                  const pctVals = sources.map(([, s]) => s.pct_norm).filter((v): v is number => v != null);
                  const avgAuto = autoVals.length > 0 ? autoVals.reduce((a, b) => a + b, 0) / autoVals.length : null;
                  const maxAuto = autoVals.length > 0 ? Math.max(...autoVals) : null;
                  const avgPct = pctVals.length > 0 ? pctVals.reduce((a, b) => a + b, 0) / pctVals.length : null;
                  const maxPct = pctVals.length > 0 ? Math.max(...pctVals) : null;
                  return (
                    <div>
                      <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Source Breakdown</p>
                      <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                        <thead>
                          <tr>
                            <th style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "left" }}>Source</th>
                            <th style={{ padding: "2px 8px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Auto-aug</th>
                            <th style={{ padding: "2px 8px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Pct</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sources.map(([src, stats]) => (
                            <tr key={src}>
                              <td style={{ padding: "2px 10px 2px 0" }}>
                                <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--bg-sidebar)", border: "1px solid var(--border)", color: "var(--text-secondary)" }}>{src}</span>
                              </td>
                              <td style={{ padding: "2px 8px", textAlign: "right" }}>
                                {stats.auto_aug != null ? stats.auto_aug.toFixed(3) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                              </td>
                              <td style={{ padding: "2px 8px", textAlign: "right" }}>
                                {stats.pct_norm != null ? fmtPctNorm(stats.pct_norm) : <span style={{ color: "var(--text-muted)" }}>—</span>}
                              </td>
                            </tr>
                          ))}
                          <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                            <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                              <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--brand-light)", border: "1px solid var(--brand)", color: "var(--brand)", fontWeight: 700 }}>AVG</span>
                            </td>
                            <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>{avgAuto != null ? avgAuto.toFixed(3) : "—"}</td>
                            <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>{avgPct != null ? fmtPctNorm(avgPct) : "—"}</td>
                          </tr>
                          <tr>
                            <td style={{ padding: "2px 10px 4px 0", fontWeight: 700 }}>
                              <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "#fffbeb", border: "1px solid #d97706", color: "#d97706", fontWeight: 700 }}>MAX</span>
                            </td>
                            <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>{maxAuto != null ? maxAuto.toFixed(3) : "—"}</td>
                            <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>{maxPct != null ? fmtPctNorm(maxPct) : "—"}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  );
                })()}
                {/* Top MCPs */}
                {row.top_mcps && row.top_mcps.length > 0 && (
                  <div style={{ minWidth: 200 }}>
                    <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Top MCP Servers</p>
                    <ul style={{ margin: 0, paddingLeft: 16, listStyleType: "disc" }}>
                      {row.top_mcps.slice(0, 5).map((mcp, mi) => (
                        <li key={mi} style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 3 }}>
                          {mcp.url
                            ? <a href={mcp.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand)", textDecoration: "underline" }}>{mcp.title}</a>
                            : mcp.title}
                          {mcp.rating != null && (
                            <span style={{ marginLeft: 6, fontSize: 10, color: "var(--text-muted)" }}>({mcp.rating.toFixed(2)})</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </td>
          </tr>
        )}

        {/* Recursive child rows */}
        {isExpanded && !isOcc && !isTask && childRowsData.map((child) =>
          renderRow(child, nextLvl, indent + 1)
        )}
      </React.Fragment>
    );
  }

  // ── Paginate all levels (keeps DOM small → no scroll jank) ──────────────
  const shownRows = topRows.slice(0, rowLimit);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - var(--nav-height))", overflow: "hidden" }}>

      {/* ── Header bar ── */}
      <div style={{
        background: "var(--bg-surface)", borderBottom: "1px solid var(--border)",
        padding: "0 20px", height: 52, display: "flex", alignItems: "center", gap: 14, flexShrink: 0,
      }}>
        <div>
          <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em", margin: 0 }}>Occupation Explorer</h1>
          <p style={{ fontSize: 11, color: "var(--text-muted)", margin: 0 }}>
            {totalOccs} occupations{totalTasks != null ? ` · ${totalTasks.toLocaleString()} tasks` : ""}
          </p>
        </div>
      </div>

      {/* ── Filter strip ── */}
      <div style={{
        background: "var(--bg-surface)", borderBottom: "1px solid var(--border)",
        padding: "10px 20px", flexShrink: 0, display: "flex", flexDirection: "column", gap: 8,
      }}>
        {/* Row 1: Major pills */}
        <div style={{ display: "flex", gap: 5, flexWrap: "nowrap", overflowX: "auto", paddingBottom: 2 }}>
          {/* All pill */}
          <button
            onClick={() => setSelectedMajors(new Set())}
            style={{
              flexShrink: 0, fontSize: 11, padding: "3px 9px", borderRadius: 12,
              border: `1.5px solid ${selectedMajors.size === 0 ? "var(--brand)" : "var(--border)"}`,
              background: selectedMajors.size === 0 ? "var(--brand-light)" : "transparent",
              color: selectedMajors.size === 0 ? "var(--brand)" : "var(--text-secondary)",
              cursor: "pointer", fontWeight: selectedMajors.size === 0 ? 600 : 400,
              whiteSpace: "nowrap",
            }}
          >All ({totalOccs})</button>
          {allMajors.map((maj) => {
            const sel = selectedMajors.has(maj);
            return (
              <button
                key={maj}
                onClick={() => {
                  setSelectedMajors((prev) => {
                    const next = new Set(prev);
                    if (next.has(maj)) next.delete(maj); else next.add(maj);
                    return next;
                  });
                }}
                style={{
                  flexShrink: 0, fontSize: 11, padding: "3px 9px", borderRadius: 12,
                  border: `1.5px solid ${sel ? "var(--brand)" : "var(--border)"}`,
                  background: sel ? "var(--brand-light)" : "transparent",
                  color: sel ? "var(--brand)" : "var(--text-secondary)",
                  cursor: "pointer", fontWeight: sel ? 600 : 400, whiteSpace: "nowrap",
                }}
              >{maj} ({majorCounts.get(maj) ?? 0})</button>
            );
          })}
        </div>

        {/* Row 2: Level + Search + Geo + Phys + Min filters */}
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {/* Level selector */}
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 5, overflow: "hidden" }}>
            {LEVEL_OPTIONS.map(({ v, l }, i) => (
              <button key={v} onClick={() => setTableLevel(v)} style={{
                padding: "4px 10px", fontSize: 11, cursor: "pointer", border: "none",
                borderRight: i < LEVEL_OPTIONS.length - 1 ? "1px solid var(--border)" : "none",
                background: tableLevel === v ? "var(--brand-light)" : "transparent",
                color: tableLevel === v ? "var(--brand)" : "var(--text-secondary)",
                fontWeight: tableLevel === v ? 600 : 400,
              }}>{l}</button>
            ))}
          </div>
          {/* Geo */}
          <BtnSeg
            opts={[{ v: "nat", l: "Nat" }, { v: "ut", l: "Utah" }]}
            val={geo}
            onChange={setGeo}
          />
          {/* Physical (hidden in simple mode) */}
          {!isSimple && (
          <BtnSeg
            opts={[{ v: "all", l: "All" }, { v: "exclude", l: "No Phys" }, { v: "only", l: "Phys only" }]}
            val={physicalMode}
            onChange={setPhysicalMode}
          />
          )}

          {/* Search */}
          <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <span style={{ position: "absolute", left: 8, color: "var(--text-muted)", pointerEvents: "none" }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                paddingLeft: 28, paddingRight: 8, paddingTop: 5, paddingBottom: 5,
                fontSize: 12, border: "1px solid var(--border)", borderRadius: 6,
                outline: "none", background: "var(--bg-surface)", color: "var(--text-primary)",
                width: 200,
              }}
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                style={{ position: "absolute", right: 6, background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: 14, lineHeight: 1, padding: 0 }}
              >×</button>
            )}
          </div>

          {/* Column selector */}
          <div ref={colSelectorRef} style={{ position: "relative" }}>
            <button
              onClick={() => setColSelectorOpen((p) => !p)}
              title="Select columns"
              style={{
                fontSize: 11, padding: "4px 8px", border: "1px solid var(--border)",
                borderRadius: 5, background: colSelectorOpen ? "var(--brand-light)" : "transparent",
                cursor: "pointer", color: colSelectorOpen ? "var(--brand)" : "var(--text-secondary)",
                display: "inline-flex", alignItems: "center", gap: 4,
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
                <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
              </svg>
              Columns
            </button>
            {colSelectorOpen && (() => {
              const selectableCols = COLUMNS.filter((c) => {
                if (c.key === "name") return false;
                if (TASK_ONLY_COLS.has(c.key) && tableLevel !== "task") return false;
                if (NON_TASK_COLS.has(c.key) && tableLevel === "task") return false;
                if (isSimpleTask && !SIMPLE_TASK_COLS.has(c.key)) return false;
                if (isSimple && !isSimpleTask && !SIMPLE_COLS.has(c.key)) return false;
                return true;
              });
              const OCC_GROUP = new Set(["occ", "broad_cat", "minor_cat", "major_cat"]);
              const WA_GROUP = new Set(["dwa_col", "iwa_col", "gwa_col"]);
              const allChecked = selectableCols.every((c) => !hiddenCols.has(c.key));
              const occCols = selectableCols.filter((c) => OCC_GROUP.has(c.key));
              const occAllChecked = occCols.length > 0 && occCols.every((c) => !hiddenCols.has(c.key));
              const waCols = selectableCols.filter((c) => WA_GROUP.has(c.key));
              const waAllChecked = waCols.length > 0 && waCols.every((c) => !hiddenCols.has(c.key));
              const pillStyle: React.CSSProperties = {
                fontSize: 10, padding: "2px 7px", border: "1px solid var(--border)",
                borderRadius: 10, background: "var(--bg-surface)", cursor: "pointer",
                color: "var(--text-secondary)", lineHeight: "16px",
              };
              return (
                <div
                  style={{
                    position: "absolute", right: 0, top: "100%", marginTop: 4,
                    background: "var(--bg-surface)", border: "1px solid var(--border)",
                    borderRadius: 8, padding: "8px 0", zIndex: 100,
                    boxShadow: "0 4px 16px rgba(0,0,0,0.12)", width: 220,
                    maxHeight: 400, overflowY: "auto",
                  }}
                >
                  {tableLevel === "task" && (
                    <div style={{ display: "flex", gap: 4, marginBottom: 6, flexWrap: "wrap", padding: "0 10px" }}>
                      <button
                        onClick={() => {
                          setHiddenCols((prev) => {
                            const next = new Set(prev);
                            if (allChecked) { selectableCols.forEach((c) => next.add(c.key)); }
                            else { selectableCols.forEach((c) => next.delete(c.key)); }
                            return next;
                          });
                        }}
                        style={pillStyle}
                      >{allChecked ? "None" : "All"}</button>
                      {occCols.length > 0 && (
                        <button
                          onClick={() => {
                            setHiddenCols((prev) => {
                              const next = new Set(prev);
                              if (occAllChecked) { occCols.forEach((c) => next.add(c.key)); }
                              else { occCols.forEach((c) => next.delete(c.key)); }
                              return next;
                            });
                          }}
                          style={pillStyle}
                        >Occ {occAllChecked ? "\u2212" : "+"}</button>
                      )}
                      {waCols.length > 0 && (
                        <button
                          onClick={() => {
                            setHiddenCols((prev) => {
                              const next = new Set(prev);
                              if (waAllChecked) { waCols.forEach((c) => next.add(c.key)); }
                              else { waCols.forEach((c) => next.delete(c.key)); }
                              return next;
                            });
                          }}
                          style={pillStyle}
                        >WA {waAllChecked ? "\u2212" : "+"}</button>
                      )}
                    </div>
                  )}
                  {selectableCols.map((c) => {
                    const checked = !hiddenCols.has(c.key);
                    const displayLabel = tableLevel === "task" && SIMPLE_TASK_LABELS[c.key] ? SIMPLE_TASK_LABELS[c.key] : c.label;
                    return (
                      <label
                        key={c.key}
                        style={{
                          display: "flex", alignItems: "center", gap: 8,
                          padding: "4px 12px", fontSize: 11, cursor: "pointer",
                          color: checked ? "var(--text-primary)" : "var(--text-muted)",
                        }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = "#f5f5f3"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => {
                            setHiddenCols((prev) => {
                              const next = new Set(prev);
                              if (next.has(c.key)) next.delete(c.key); else next.add(c.key);
                              return next;
                            });
                          }}
                          style={{ margin: 0 }}
                        />
                        {displayLabel}
                      </label>
                    );
                  })}
                </div>
              );
            })()}
          </div>

          {/* Reset */}
          <button
            onClick={handleReset}
            style={{
              fontSize: 11, padding: "4px 12px", borderRadius: 5,
              border: "1px solid var(--border)", background: "transparent",
              color: "var(--text-secondary)", cursor: "pointer",
            }}
          >Reset</button>

          {/* Showing count */}
          <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
            {topRows.length} rows
          </span>
        </div>

        {/* Row 3: PctComputePanel (hidden in simple mode — auto-computed) */}
        {!isSimple && (
          <PctComputePanel config={config} geo={geo} tableLevel={tableLevel} onResult={setPctAffectedMap} />
        )}

        {/* % Tasks Affected slider (shown when map computed, hidden in simple mode) */}
        {pctAffectedMap && !isSimple && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 11, color: "var(--text-secondary)", whiteSpace: "nowrap" }}>
              % Tasks Aff. &ge; {minPctAffected.toFixed(0)}%
            </span>
            <input
              type="range"
              min={0} max={100} step={1}
              value={minPctAffected}
              onChange={(e) => setMinPctAffected(Number(e.target.value))}
              style={{ width: 160 }}
            />
          </div>
        )}
      </div>

      {/* ── Table ── */}
      <div style={{ flex: 1, overflowY: "auto", overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>

          {/* Sticky header */}
          <thead>
            <tr style={{
              position: "sticky", top: 0,
              background: "var(--bg-surface)", zIndex: 10,
              borderBottom: "2px solid var(--border)",
            }}>
              {visibleCols.map((col) => {
                const isSorted = sortCol === col.key;
                const hasFilter = colFilters[col.key]?.min !== "" || colFilters[col.key]?.max !== "";
                return (
                  <th
                    key={col.key}
                    style={{
                      padding: "7px 8px",
                      textAlign: !col.numeric ? "left" : "right",
                      fontSize: 11,
                      fontWeight: 700,
                      color: isSorted ? "var(--brand)" : "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      width: col.width,
                      cursor: "pointer",
                      userSelect: "none",
                      position: "relative",
                    }}
                    onClick={() => handleSort(col.key)}
                  >
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 3, paddingRight: (col.numeric || TEXT_FILTER_COLS.has(col.key)) ? 14 : 0 }}>
                      {col.label}
                      {col.tooltip && <InfoTooltip text={col.tooltip} />}
                      {isSorted && (
                        <span style={{ color: "var(--brand)", fontSize: 10 }}>
                          {sortDir === "desc" ? "↓" : "↑"}
                        </span>
                      )}
                    </div>
                    {col.numeric && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenFilter((prev) => prev === col.key ? null : col.key);
                        }}
                        style={{
                          position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)",
                          cursor: "pointer",
                          color: hasFilter ? "var(--brand)" : "var(--text-muted)",
                          opacity: hasFilter ? 1 : 0.5,
                          display: "inline-flex",
                        }}
                        title="Filter"
                      >
                        <FunnelIcon />
                      </span>
                    )}
                    {openFilter === col.key && (
                      <ColumnFilterDropdown
                        colKey={col.key}
                        filters={colFilters}
                        setFilters={setColFilters}
                        onClose={() => setOpenFilter(null)}
                      />
                    )}
                    {TEXT_FILTER_COLS.has(col.key) && (() => {
                      const hasTextFilter = textColFilters[col.key] !== null && textColFilters[col.key] !== undefined;
                      return (
                        <>
                          <span
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenTextFilter((prev) => prev === col.key ? null : col.key);
                            }}
                            style={{
                              position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)",
                              cursor: "pointer",
                              color: hasTextFilter ? "var(--brand)" : "var(--text-muted)",
                              opacity: hasTextFilter ? 1 : 0.5,
                              display: "inline-flex",
                            }}
                            title="Filter values"
                          >
                            <FunnelIcon />
                          </span>
                          {openTextFilter === col.key && (
                            <TextColumnFilterDropdown
                              colKey={col.key}
                              uniqueValues={textColUniqueValues[col.key] ?? []}
                              selectedValues={textColFilters[col.key] ?? null}
                              onSelectionChange={(ck, vals) => setTextColFilters((prev) => ({ ...prev, [ck]: vals }))}
                              onClose={() => setOpenTextFilter(null)}
                            />
                          )}
                        </>
                      );
                    })()}
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody>
            {/* Task level loading */}
            {tableLevel === "task" && taskLoading && (
              <tr>
                <td colSpan={visibleCols.length} style={{ padding: "40px", textAlign: "center" }}>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 20, height: 20, borderRadius: "50%", border: "2px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
                    <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading tasks…</span>
                  </div>
                </td>
              </tr>
            )}

            {/* No rows */}
            {!taskLoading && topRows.length === 0 && (
              <tr>
                <td colSpan={visibleCols.length} style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
                  No rows match the current filters.
                </td>
              </tr>
            )}

            {/* Data rows */}
            {!taskLoading && shownRows.map((row: FlatRow) =>
              renderRow(row, tableLevel, 0)
            )}
          </tbody>
        </table>

        {/* Pagination footer — applies to all levels */}
        {!taskLoading && topRows.length > rowLimit && (
          <div style={{ padding: "14px 20px", textAlign: "center", borderTop: "1px solid var(--border-light)" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)", marginRight: 12 }}>
              Showing {Math.min(rowLimit, topRows.length)} of {topRows.length} rows.
            </span>
            <button
              onClick={() => setRowLimit((r) => r + 100)}
              style={{
                fontSize: 12, color: "var(--brand)", background: "none", border: "none",
                cursor: "pointer", padding: 0, fontWeight: 600,
              }}
            >Load 100 more →</button>
          </div>
        )}
      </div>

      {/* Spin animation */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
