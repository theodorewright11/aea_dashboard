"use client";

import React, {
  useState,
  useMemo,
  useCallback,
  useEffect,
  useRef,
} from "react";
import { createPortal } from "react-dom";
import type { WAExplorerRow, WATaskDetail, ConfigResponse, EcoTaskRow, TaskSourceStats, ActivityRow, McpEntry } from "@/lib/types";
import { fetchWAActivityTasks, fetchWorkActivities, fetchAllEcoTasks } from "@/lib/api";
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
  rows: WAExplorerRow[];
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

const TASK_ONLY_COLS = new Set(["occ", "major_cat", "minor_cat", "broad_cat", "dwa_col", "iwa_col", "gwa_col", "phys_col", "freq_col", "imp_col", "rel_col"]);
const NON_TASK_COLS = new Set(["n_occs", "n_tasks", "auto_avg_all", "auto_max_all", "pct_phys", "pct_avg_all", "pct_max_all", "sum_pct_avg", "sum_pct_max"]);
const TASK_LABEL_OVERRIDES: Record<string, string> = {
  auto_avg_w: "Auto Avg",
  auto_max_w: "Auto Max",
  pct_avg_w: "Pct Avg",
  pct_max_w: "Pct Max",
};
const TEXT_FILTER_COLS = new Set(["occ", "major_cat", "minor_cat", "broad_cat", "dwa_col", "iwa_col", "gwa_col"]);

const COLUMNS: ColDef[] = [
  { key: "name",         label: "Name",            width: 300, numeric: false },
  { key: "occ",          label: "Occupation",      width: 200, numeric: false, tooltip: "Occupation this task belongs to" },
  { key: "broad_cat",    label: "Broad",           width: 180, numeric: false, tooltip: "Broad occupation" },
  { key: "minor_cat",    label: "Minor",           width: 180, numeric: false, tooltip: "Minor occupation category" },
  { key: "major_cat",    label: "Major",           width: 180, numeric: false, tooltip: "Major occupation category" },
  { key: "dwa_col",      label: "DWA",             width: 220, numeric: false, tooltip: "Detailed Work Activity" },
  { key: "iwa_col",      label: "IWA",             width: 200, numeric: false, tooltip: "Intermediate Work Activity" },
  { key: "gwa_col",      label: "GWA",             width: 180, numeric: false, tooltip: "Generalized Work Activity" },
  { key: "emp",          label: "Emp",              width: 90,  numeric: true,  tooltip: "Total employment (BLS OEWS 2024) across occupations in this activity" },
  { key: "wage",         label: "Med Wage",         width: 90,  numeric: true,  tooltip: "Employment-weighted median annual wage" },
  { key: "phys_col",     label: "Phys",             width: 52,  numeric: false, tooltip: "Physical task (requires physical presence)" },
  { key: "freq_col",     label: "Freq",             width: 70,  numeric: true,  tooltip: "O*NET task frequency (0\u201310)" },
  { key: "imp_col",      label: "Imp",              width: 70,  numeric: true,  tooltip: "O*NET task importance (0\u20135)" },
  { key: "rel_col",      label: "Rel",              width: 70,  numeric: true,  tooltip: "O*NET task relevance (0\u2013100)" },
  { key: "n_occs",       label: "# Occs",           width: 65,  numeric: true,  tooltip: "Number of unique occupations that include tasks in this activity" },
  { key: "n_tasks",      label: "# Tasks",          width: 65,  numeric: true,  tooltip: "Number of unique tasks in this activity" },
  { key: "auto_avg_w",   label: "Auto Avg\u2191",   width: 90,  numeric: true,  tooltip: "Avg of per-task avg auto-aug score across sources (0\u20135). Only tasks with at least one source value." },
  { key: "auto_max_w",   label: "Auto Max\u2191",   width: 90,  numeric: true,  tooltip: "Avg of per-task max auto-aug score across sources (0\u20135). Only tasks with at least one source value." },
  { key: "auto_avg_all", label: "Auto Avg (all)",   width: 100, numeric: true,  tooltip: "Avg of per-task avg auto-aug (0 for tasks with no value) across ALL tasks." },
  { key: "auto_max_all", label: "Auto Max (all)",   width: 100, numeric: true,  tooltip: "Avg of per-task max auto-aug (0 for tasks with no value) across ALL tasks." },
  { key: "pct_phys",     label: "% Phys",           width: 72,  numeric: true,  tooltip: "Fraction of tasks classified as requiring physical presence." },
  { key: "pct_avg_w",    label: "Pct Avg\u2191",    width: 90,  numeric: true,  tooltip: "Avg of per-task avg pct (share of AI conversations) across sources. Only tasks with a value." },
  { key: "pct_max_w",    label: "Pct Max\u2191",    width: 90,  numeric: true,  tooltip: "Avg of per-task max pct across sources. Only tasks with a value." },
  { key: "pct_avg_all",  label: "Pct Avg (all)",    width: 100, numeric: true,  tooltip: "Avg pct across ALL tasks (0 for tasks with no value)." },
  { key: "pct_max_all",  label: "Pct Max (all)",    width: 100, numeric: true,  tooltip: "Max pct averaged across ALL tasks (0 for no value)." },
  { key: "sum_pct_avg",  label: "\u03A3 Pct Avg",   width: 90,  numeric: true,  tooltip: "Sum of per-task avg pct across all tasks with a value." },
  { key: "sum_pct_max",  label: "\u03A3 Pct Max",   width: 90,  numeric: true,  tooltip: "Sum of per-task max pct across all tasks with a value." },
  { key: "pct_affected", label: "% Tasks Aff.",     width: 100, numeric: true,  tooltip: "% Tasks Affected from the compute panel. Uses the selected datasets and method." },
  { key: "workers_aff",  label: "Workers Aff.",      width: 110, numeric: true,  tooltip: "Workers affected = % Tasks Affected × employment. Requires compute panel result." },
  { key: "wages_aff",    label: "Wages Aff. ($B)",   width: 120, numeric: true,  tooltip: "Wages affected (billions) = % Tasks Affected × employment × median wage. Requires compute panel result." },
];

// ── Display row model ──────────────────────────────────────────────────────────

interface DisplayRow {
  name: string;
  rowId?: string;
  level: "gwa" | "iwa" | "dwa";
  gwa: string | null;
  parent: string | null;
  gwa_title?: string | null;
  iwa_title?: string | null;
  dwa_title?: string | null;
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
  pct_affected?: number | null;
  // Task-level fields
  title_current?: string | null;
  major_occ_category?: string | null;
  minor_occ_category?: string | null;
  broad_occ?: string | null;
  physical?: boolean | null;
  freq_mean?: number | null;
  importance?: number | null;
  relevance?: number | null;
  sources?: Record<string, TaskSourceStats>;
  top_mcps?: McpEntry[];
}

function waRowToDisplay(row: WAExplorerRow, geo: "nat" | "ut", empW: "freq" | "value" = "freq"): DisplayRow {
  const emp = empW === "freq"
    ? (geo === "nat" ? row.emp_nat_freq : row.emp_ut_freq)
    : (geo === "nat" ? row.emp_nat_value : row.emp_ut_value);
  const wage = empW === "freq"
    ? (geo === "nat" ? row.wage_nat_freq : row.wage_ut_freq)
    : (geo === "nat" ? row.wage_nat_value : row.wage_ut_value);
  return {
    name: row.name,
    level: row.level,
    gwa: row.gwa ?? null,
    parent: row.parent ?? null,
    emp: emp ?? 0,
    wage: wage ?? null,
    n_occs: row.n_occs,
    n_tasks: row.n_tasks,
    auto_avg_with_vals: row.auto_avg_with_vals ?? null,
    auto_max_with_vals: row.auto_max_with_vals ?? null,
    auto_avg_all: row.auto_avg_all ?? null,
    auto_max_all: row.auto_max_all ?? null,
    pct_physical: row.pct_physical ?? null,
    pct_avg_with_vals: row.pct_avg_with_vals ?? null,
    pct_max_with_vals: row.pct_max_with_vals ?? null,
    pct_avg_all: row.pct_avg_all ?? null,
    pct_max_all: row.pct_max_all ?? null,
    sum_pct_avg: row.sum_pct_avg ?? null,
    sum_pct_max: row.sum_pct_max ?? null,
  };
}

// ── Column value getter ────────────────────────────────────────────────────────

function getVal(row: DisplayRow, col: string): number | null {
  switch (col) {
    case "emp":          return row.emp;
    case "wage":         return row.wage;
    case "freq_col":     return row.freq_mean ?? null;
    case "imp_col":      return row.importance ?? null;
    case "rel_col":      return row.relevance ?? null;
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
    case "pct_affected": return row.pct_affected ?? null;
    case "workers_aff": {
      const pct = row.pct_affected;
      return pct != null ? (pct / 100) * row.emp : null;
    }
    case "wages_aff": {
      const pct = row.pct_affected;
      return (pct != null && row.wage != null) ? (pct / 100) * row.emp * row.wage / 1e9 : null;
    }
    default:             return null;
  }
}

// ── Cell renderer ──────────────────────────────────────────────────────────────

function AutoCell({ v }: { v: number | null | undefined }) {
  if (v == null) return <span style={{ color: "var(--text-muted)" }}>—</span>;
  return (
    <span style={{ color: v > 0 ? "var(--brand)" : "var(--text-muted)" }}>
      {fmtAutoAug(v)}
    </span>
  );
}

function renderCell(col: string, row: DisplayRow): React.ReactNode {
  const muted = { color: "var(--text-muted)" } as React.CSSProperties;
  switch (col) {
    case "occ":          return row.title_current ?? <span style={muted}>—</span>;
    case "broad_cat":    return row.broad_occ ?? <span style={muted}>—</span>;
    case "minor_cat":    return row.minor_occ_category ?? <span style={muted}>—</span>;
    case "major_cat":    return row.major_occ_category ?? <span style={muted}>—</span>;
    case "dwa_col":      return row.dwa_title ?? <span style={muted}>—</span>;
    case "iwa_col":      return row.iwa_title ?? <span style={muted}>—</span>;
    case "gwa_col":      return row.gwa ?? <span style={muted}>—</span>;
    case "emp":          return fmtEmp(row.emp);
    case "wage":         return fmtWage(row.wage);
    case "phys_col": {
      if (row.physical === true) return <span style={{ color: "#16a34a", fontSize: 11 }}>✓</span>;
      if (row.physical === false) return <span style={{ color: "var(--text-muted)", fontSize: 11 }}>✗</span>;
      return <span style={muted}>—</span>;
    }
    case "freq_col":     return row.freq_mean != null ? row.freq_mean.toFixed(2) : <span style={muted}>—</span>;
    case "imp_col":      return row.importance != null ? row.importance.toFixed(2) : <span style={muted}>—</span>;
    case "rel_col":      return row.relevance != null ? row.relevance.toFixed(2) : <span style={muted}>—</span>;
    case "n_occs":       return row.n_occs;
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
    case "pct_affected": {
      const v = row.pct_affected;
      return v != null
        ? <span style={{ color: "var(--brand)", fontWeight: 500 }}>{v.toFixed(2)}%</span>
        : <span style={muted}>—</span>;
    }
    case "workers_aff": {
      const pct = row.pct_affected;
      if (pct == null) return <span style={muted}>—</span>;
      return <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtEmp((pct / 100) * row.emp)}</span>;
    }
    case "wages_aff": {
      const pct = row.pct_affected;
      if (pct == null || row.wage == null) return <span style={muted}>—</span>;
      const rawDollars = (pct / 100) * row.emp * row.wage;
      const fmtWagesAff = rawDollars >= 1e9 ? `$${(rawDollars / 1e9).toFixed(2)}B`
        : rawDollars >= 1e6 ? `$${(rawDollars / 1e6).toFixed(2)}M`
        : rawDollars >= 1e3 ? `$${(rawDollars / 1e3).toFixed(0)}K`
        : `$${rawDollars.toFixed(0)}`;
      return <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtWagesAff}</span>;
    }
    default: return <span style={muted}>—</span>;
  }
}

// ── Text highlight helper ──────────────────────────────────────────────────────

function highlightText(text: string, query: string): React.ReactNode {
  if (!query) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return text;
  return (
    <>
      {text.slice(0, idx)}
      <mark style={{ background: "#fef08a", borderRadius: 2 }}>
        {text.slice(idx, idx + query.length)}
      </mark>
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
      style={{
        transform: open ? "rotate(0deg)" : "rotate(-90deg)",
        transition: "transform 0.18s ease",
        flexShrink: 0,
        color: "var(--text-muted)",
      }}
      aria-hidden="true"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function FunnelIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true">
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

// ── Text column filter dropdown (multi-select values) ─────────────────────────

function TextColumnFilterDropdown({
  colKey,
  values,
  selected,
  setFilters,
  onClose,
}: {
  colKey: string;
  values: string[];
  selected: string[];
  setFilters: React.Dispatch<React.SetStateAction<Record<string, string[]>>>;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  const toggle = (v: string) => {
    setFilters((prev) => {
      const cur = prev[colKey] ?? [];
      const next = cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v];
      return { ...prev, [colKey]: next };
    });
  };

  return (
    <div ref={ref} style={{
      position: "absolute", top: "100%", right: 0, zIndex: 500,
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 7, padding: "6px 0", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      minWidth: 180, maxWidth: 260, maxHeight: 280, overflowY: "auto",
    }}>
      {selected.length > 0 && (
        <button
          onClick={() => setFilters((prev) => ({ ...prev, [colKey]: [] }))}
          style={{ fontSize: 10, color: "var(--brand)", background: "none", border: "none", cursor: "pointer", padding: "2px 10px 6px", display: "block" }}
        >Clear ({selected.length})</button>
      )}
      {values.map((v) => (
        <label key={v} style={{
          display: "flex", alignItems: "center", gap: 6,
          padding: "3px 10px", fontSize: 11, cursor: "pointer",
          color: selected.includes(v) ? "var(--brand)" : "var(--text-primary)",
        }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#f5f5f3"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
        >
          <input type="checkbox" checked={selected.includes(v)} onChange={() => toggle(v)} style={{ margin: 0, flexShrink: 0 }} />
          <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v}</span>
        </label>
      ))}
      {values.length === 0 && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", padding: "4px 10px", margin: 0 }}>No values</p>
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

// ── Task sub-table for expanded DWA rows ───────────────────────────────────────

function WATaskSubRow({ task, geo, empWeighting }: { task: WATaskDetail; geo: "nat" | "ut"; empWeighting: "freq" | "value" }) {
  const [expanded, setExpanded] = useState(false);

  const avgAuto = task.avg_auto_aug;
  const maxAuto = task.max_auto_aug;
  const avgPct  = task.avg_pct_norm;
  const maxPct  = task.max_pct_norm;
  const barPct  = avgAuto != null ? Math.min(avgAuto / 5, 1) * 100 : null;
  const emp     = empWeighting === "freq"
    ? (geo === "nat" ? task.emp_nat_freq : task.emp_ut_freq)
    : (geo === "nat" ? task.emp_nat_value : task.emp_ut_value);
  const wage    = empWeighting === "freq" ? task.wage_nat_freq : task.wage_nat_value;
  const sources = Object.entries(task.sources ?? {});
  const muted = { color: "var(--text-muted)" } as React.CSSProperties;
  const topMcps = task.top_mcps ?? [];

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "6px 10px", fontSize: 11, color: "var(--text-primary)", verticalAlign: "top", maxWidth: 340 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 5 }}>
            <ChevronIcon open={expanded} />
            <span style={{ lineHeight: 1.4 }}>{task.task}</span>
          </div>
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 80, verticalAlign: "top" }}>
          {fmtEmp(emp)}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 80, verticalAlign: "top" }}>
          {fmtWage(wage)}
        </td>
        <td style={{ padding: "6px 6px", textAlign: "center", verticalAlign: "top", width: 44 }}>
          {task.physical === true
            ? <span style={{ color: "#16a34a", fontSize: 11 }}>✓</span>
            : task.physical === false
            ? <span style={{ color: "var(--text-muted)", fontSize: 11 }}>✗</span>
            : <span style={{ color: "var(--text-muted)", fontSize: 10 }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 64, verticalAlign: "top" }}>
          {task.freq_mean != null ? task.freq_mean.toFixed(2) : <span style={muted}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 56, verticalAlign: "top" }}>
          {task.importance != null ? task.importance.toFixed(2) : <span style={muted}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 56, verticalAlign: "top" }}>
          {task.relevance != null ? task.relevance.toFixed(2) : <span style={muted}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", verticalAlign: "top", width: 100 }}>
          {barPct != null ? (
            <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
              <div style={{ width: 48, height: 5, background: "var(--border)", borderRadius: 3, overflow: "hidden", flexShrink: 0 }}>
                <div style={{ width: `${barPct}%`, height: "100%", background: "var(--brand)", borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 10, color: "var(--text-secondary)" }}>{avgAuto?.toFixed(2)}</span>
            </div>
          ) : <span style={{ fontSize: 10, color: "var(--text-muted)" }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 72, verticalAlign: "top" }}>
          {fmtAutoAug(maxAuto)}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, textAlign: "right", width: 80, verticalAlign: "top" }}>
          {avgPct != null
            ? <span style={{ color: "var(--brand)" }}>{fmtPctNorm(avgPct)}</span>
            : <span style={{ color: "var(--text-muted)" }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, textAlign: "right", width: 80, verticalAlign: "top" }}>
          {maxPct != null
            ? <span style={{ color: "var(--brand)" }}>{fmtPctNorm(maxPct)}</span>
            : <span style={{ color: "var(--text-muted)" }}>—</span>}
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#fafaf8", borderBottom: "1px solid var(--border-light)" }}>
          <td colSpan={11} style={{ padding: "10px 20px 14px 28px" }}>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              {/* Occupation Categories */}
              {task.title_current && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>
                    Occupation Categories
                  </p>
                  <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Occ:</b> {task.title_current}</p>
                  {task.broad_occ && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Broad:</b> {task.broad_occ}</p>}
                  {task.minor_occ_category && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Minor:</b> {task.minor_occ_category}</p>}
                  {task.major_occ_category && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>Major:</b> {task.major_occ_category}</p>}
                </div>
              )}
              {/* Work Activities */}
              {(task.gwa_title || task.iwa_title || task.dwa_title) && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>
                    Work Activities
                  </p>
                  {task.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {task.gwa_title}</p>}
                  {task.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {task.iwa_title}</p>}
                  {task.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {task.dwa_title}</p>}
                </div>
              )}
              {/* Task Detail */}
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Task Detail</p>
                <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                  <tbody>
                    <tr>
                      <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Emp</td>
                      <td style={{ padding: "2px 0" }}>{fmtEmp(emp)}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Wage</td>
                      <td style={{ padding: "2px 0" }}>{fmtWage(wage)}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Physical</td>
                      <td style={{ padding: "2px 0" }}>
                        {task.physical === true ? <span style={{ color: "#16a34a" }}>✓ Yes</span> : task.physical === false ? <span style={muted}>✗ No</span> : <span style={muted}>—</span>}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Freq</td>
                      <td style={{ padding: "2px 0" }}>{task.freq_mean != null ? task.freq_mean.toFixed(2) : <span style={muted}>—</span>}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Imp</td>
                      <td style={{ padding: "2px 0" }}>{task.importance != null ? task.importance.toFixed(2) : <span style={muted}>—</span>}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Rel</td>
                      <td style={{ padding: "2px 0" }}>{task.relevance != null ? task.relevance.toFixed(2) : <span style={muted}>—</span>}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              {/* Source Breakdown */}
              {sources.length > 0 && (
                <div>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>
                    Source Breakdown
                  </p>
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
                            {stats.auto_aug != null ? stats.auto_aug.toFixed(3) : <span style={muted}>—</span>}
                          </td>
                          <td style={{ padding: "2px 8px", textAlign: "right" }}>
                            {stats.pct_norm != null ? fmtPctNorm(stats.pct_norm) : <span style={muted}>—</span>}
                          </td>
                        </tr>
                      ))}
                      <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                        <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                          <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--brand-light)", border: "1px solid var(--brand)", color: "var(--brand)", fontWeight: 700 }}>AVG</span>
                        </td>
                        <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>
                          {avgAuto != null ? avgAuto.toFixed(3) : <span style={muted}>—</span>}
                        </td>
                        <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>
                          {avgPct != null ? fmtPctNorm(avgPct) : <span style={muted}>—</span>}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: "2px 10px 4px 0", fontWeight: 700 }}>
                          <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "#fffbeb", border: "1px solid #d97706", color: "#d97706", fontWeight: 700 }}>MAX</span>
                        </td>
                        <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>
                          {maxAuto != null ? maxAuto.toFixed(3) : <span style={muted}>—</span>}
                        </td>
                        <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>
                          {maxPct != null ? fmtPctNorm(maxPct) : <span style={muted}>—</span>}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
              {/* Top MCP Servers */}
              {topMcps.length > 0 && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>
                    Top MCP Servers
                  </p>
                  <ol style={{ margin: 0, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 3 }}>
                    {topMcps.slice(0, 5).map((mcp, i) => (
                      <li key={i} style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                        {mcp.url
                          ? <a href={mcp.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand)", textDecoration: "none" }}>{mcp.title}</a>
                          : <span>{mcp.title}</span>}
                        {mcp.rating != null && <span style={{ color: "var(--text-muted)", marginLeft: 4 }}>({mcp.rating.toFixed(1)})</span>}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function WATaskSubHeader({ geo }: { geo: "nat" | "ut" }) {
  return (
    <tr style={{ borderBottom: "2px solid var(--border)" }}>
      <th style={{ padding: "5px 10px 5px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Task</th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Emp {geo === "ut" ? "(UT)" : "(Nat)"}
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Med Wage
      </th>
      <th style={{ padding: "5px 6px", textAlign: "center", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 44 }}>Phys</th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 64, whiteSpace: "nowrap" }}>
        Freq
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 56, whiteSpace: "nowrap" }}>
        Imp
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 56, whiteSpace: "nowrap" }}>
        Rel
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

// ── Level badge ────────────────────────────────────────────────────────────────

function LevelBadge({ level }: { level: "gwa" | "iwa" | "dwa" }) {
  const color = level === "gwa" ? "#3a5f83" : level === "iwa" ? "#4a7c6f" : "#7c6f4a";
  return (
    <span style={{
      fontSize: 9, fontWeight: 700, padding: "1px 5px", borderRadius: 3,
      background: `${color}18`, border: `1px solid ${color}44`, color,
      textTransform: "uppercase", letterSpacing: "0.06em", flexShrink: 0,
    }}>
      {level}
    </span>
  );
}

// ── WALevel type ───────────────────────────────────────────────────────────────

type WALevel = "gwa" | "iwa" | "dwa" | "task";
type SortDir = "asc" | "desc";

// ── WA % Tasks Affected compute panel ─────────────────────────────────────────

interface WaPctSettings {
  datasets: string[];
  combineMethod: "Average" | "Max";
  method: "freq" | "imp";
  geo: "nat" | "ut";
  physicalMode: "all" | "exclude" | "only";
  useAutoAug: boolean;
  useAdjMean: boolean;
}

function WaPctComputePanel({
  config,
  geo,
  viewLevel,
  onResult,
  empWeighting,
}: {
  config: ConfigResponse;
  geo: "nat" | "ut";
  viewLevel: WALevel;
  onResult: (map: Map<string, number> | null) => void;
  empWeighting: "freq" | "value";
}) {
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState<WaPctSettings>({
    datasets: ["AEI v4"],
    combineMethod: "Average",
    method: "freq",
    geo,
    physicalMode: "all",
    useAutoAug: false,
    useAdjMean: false,
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

  // Sync method from empWeighting toggle: "freq" -> "freq", "value" -> "imp"
  const empWeightingChangedRef = useRef(false);
  useEffect(() => {
    const newMethod = empWeighting === "value" ? "imp" : "freq";
    setSettings((s) => {
      if (s.method !== newMethod) empWeightingChangedRef.current = true;
      return { ...s, method: newMethod };
    });
  }, [empWeighting]);

  function set<K extends keyof WaPctSettings>(k: K, v: WaPctSettings[K]) {
    setSettings((s) => ({ ...s, [k]: v }));
  }

  const hasMCP = settings.datasets.some((d) => d.startsWith("MCP"));

  // Check if datasets are AEI-family (cannot mix)
  const hasAEI = settings.datasets.some((d) => d.startsWith("AEI"));
  const hasMCPorMS = settings.datasets.some((d) => d.startsWith("MCP") || d === "Microsoft");
  const isMixed = hasAEI && hasMCPorMS;

  const compute = useCallback(async () => {
    if (!settings.datasets.length || isMixed) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchWorkActivities({
        selectedDatasets: settings.datasets,
        combineMethod: settings.combineMethod,
        method: settings.method,
        useAutoAug: settings.useAutoAug,
        useAdjMean: settings.useAutoAug && settings.useAdjMean,
        physicalMode: settings.physicalMode,
        geo: settings.geo,
        aggLevel: "major", // not used by WA endpoint but required
        sortBy: "Workers Affected",
        topN: 5000,
        searchQuery: "",
        contextSize: 5,
      });
      // Extract pct from ALL levels so accordion children can look up values
      const group = resp.aei_group ?? resp.mcp_group;
      if (!group) { setError("No data returned"); setLoading(false); return; }
      const map = new Map<string, number>();
      (["gwa", "iwa", "dwa"] as const).forEach((lvl) => {
        const actRows: ActivityRow[] = group[lvl] ?? [];
        actRows.forEach((r) => map.set(r.category, r.pct_tasks_affected));
      });
      onResult(map);
      setComputed(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Compute failed");
    } finally {
      setLoading(false);
    }
  }, [settings, onResult, isMixed]);

  // Auto-recompute when geo changes while already computed
  useEffect(() => {
    if (geoChangedRef.current && computed && !loading) {
      geoChangedRef.current = false;
      compute();
    }
  }, [settings.geo, computed, loading, compute]);

  // Auto-recompute when empWeighting changes while already computed
  useEffect(() => {
    if (empWeightingChangedRef.current && computed && !loading) {
      empWeightingChangedRef.current = false;
      compute();
    }
  }, [settings.method, computed, loading, compute]);

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden", marginTop: 4 }}>
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
          {isMixed && (
            <p style={{ fontSize: 11, color: "#b91c1c", margin: 0 }}>
              Cannot mix AEI and MCP/Microsoft datasets — they use different baselines.
            </p>
          )}
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
              {hasMCP && settings.useAutoAug && (
                <div>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>MCP adj mean</p>
                  <BtnSeg opts={[{ v: "false", l: "Off" }, { v: "true", l: "On" }]} val={String(settings.useAdjMean)} onChange={(v) => set("useAdjMean", v === "true")} />
                </div>
              )}
              <button
                onClick={compute}
                disabled={loading || !settings.datasets.length || isMixed}
                className="btn-brand"
                style={{ padding: "6px 18px", fontSize: 12, opacity: (loading || !settings.datasets.length || isMixed) ? 0.5 : 1 }}
              >
                {loading ? "Computing…" : "Compute %"}
              </button>
            </div>
          </div>
          {error && <p style={{ fontSize: 11, color: "#b91c1c", margin: 0 }}>Error: {error}</p>}
          {computed && <p style={{ fontSize: 11, color: "#16a34a", margin: 0 }}>Computed for {viewLevel.toUpperCase()} level — use slider to filter rows.</p>}
        </div>
      )}
    </div>
  );
}

// ── Main WAExplorerView ────────────────────────────────────────────────────────

// Columns visible in simple mode (activity levels: gwa/iwa/dwa)
const WA_SIMPLE_COLS = new Set([
  "name", "emp", "wage", "n_occs", "n_tasks",
  "auto_avg_all",
  "pct_avg_all", "sum_pct_avg",
  "pct_affected", "workers_aff", "wages_aff",
]);

// Columns visible in simple mode at task level
const WA_SIMPLE_TASK_COLS = new Set([
  "name", "occ", "major_cat", "gwa_col",
  "emp", "wage",
  "auto_avg_w", "pct_avg_w",
  "pct_affected", "workers_aff", "wages_aff",
]);

export default function WAExplorerView({ rows, config }: Props) {
  const { isSimple } = useSimpleMode();

  // ── State ──────────────────────────────────────────────────────────────────
  const [viewLevel, setViewLevel]   = useState<WALevel>("gwa");
  const [selectedGwas, setSelectedGwas] = useState<Set<string>>(new Set());
  const [search, setSearch]         = useState("");
  const [sortCol, setSortCol]       = useState<string>("emp");
  const [sortDir, setSortDir]       = useState<SortDir>("desc");
  const [colFilters, setColFilters] = useState<Record<string, { min: string; max: string }>>({});
  const [openFilter, setOpenFilter] = useState<string | null>(null);
  const [textColFilters, setTextColFilters] = useState<Record<string, string[]>>({});
  const [openTextFilter, setOpenTextFilter] = useState<string | null>(null);
  const [geo, setGeo]               = useState<"nat" | "ut">("nat");
  const [physicalMode, setPhysicalMode] = useState<"all" | "exclude" | "only">("all");
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [rowTasks, setRowTasks]     = useState<Record<string, WATaskDetail[] | "loading" | "error">>({});
  const [pctAffectedMap, setPctAffectedMap] = useState<Map<string, number> | null>(null);
  const [minPctAffected, setMinPctAffected] = useState(0);
  const [taskData, setTaskData]     = useState<EcoTaskRow[] | null>(null);
  const [taskLoading, setTaskLoading] = useState(false);
  const [rowLimit, setRowLimit]     = useState(100);
  const [empWeighting, setEmpWeighting] = useState<"freq" | "value">("freq");
  const [computeGeneration, setComputeGeneration] = useState(0);

  // ── Debounced search ──────────────────────────────────────────────────────
  const debouncedSearch = useDebounce(search, 250);

  // ── Column selector state (persisted to localStorage) ──────────────────
  const [hiddenCols, setHiddenCols] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set<string>();
    try {
      const saved = localStorage.getItem("aea_wa_explorer_hidden_cols");
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
    try { localStorage.setItem("aea_wa_explorer_hidden_cols", JSON.stringify(Array.from(hiddenCols))); } catch { /* silent */ }
  }, [hiddenCols]);

  // ── Auto-compute pct with WA simple-mode defaults (all AEI datasets) ────
  // Runs on mount (both simple and advanced modes), on geo change, and on reset.
  useEffect(() => {
    const aeiDatasets = config.datasets.filter(
      (d) => d.startsWith("AEI") && config.dataset_availability[d],
    );
    if (aeiDatasets.length === 0) return;
    let cancelled = false;
    fetchWorkActivities({
      selectedDatasets: aeiDatasets,
      combineMethod: "Average",
      method: "freq",
      useAutoAug: true,
      useAdjMean: true,
      physicalMode: "all",
      geo,
      aggLevel: "major",
      sortBy: "Workers Affected",
      topN: 5000,
      searchQuery: "",
      contextSize: 5,
    }).then((resp) => {
      if (cancelled) return;
      const group = resp.aei_group ?? resp.mcp_group;
      if (!group) return;
      const map = new Map<string, number>();
      (["gwa", "iwa", "dwa"] as const).forEach((lvl) => {
        const actRows: ActivityRow[] = group[lvl] ?? [];
        actRows.forEach((r) => map.set(r.category, r.pct_tasks_affected));
      });
      setPctAffectedMap(map);
    }).catch(() => { /* silent */ });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [geo, config.datasets, config.dataset_availability, computeGeneration]);

  // ── Reset row limit when filters/level change ────────────────────────────
  useEffect(() => { setRowLimit(100); }, [viewLevel, selectedGwas, debouncedSearch, colFilters, textColFilters, physicalMode, pctAffectedMap, minPctAffected, sortCol, sortDir]);

  // ── Load task data when task level selected ──────────────────────────────
  useEffect(() => {
    if (viewLevel === "task" && taskData === null && !taskLoading) {
      setTaskLoading(true);
      fetchAllEcoTasks()
        .then((res: { tasks: EcoTaskRow[] }) => setTaskData(res.tasks))
        .catch(() => setTaskData([]))
        .finally(() => setTaskLoading(false));
    }
  }, [viewLevel, taskData, taskLoading]);

  // ── Derived: GWA pill names ────────────────────────────────────────────────
  const allGwas = useMemo(() => {
    return Array.from(new Set(rows.filter((r) => r.level === "gwa").map((r) => r.name))).sort();
  }, [rows]);

  // ── Build top-level display rows ───────────────────────────────────────────
  const topRows = useMemo<DisplayRow[]>(() => {
    const searchQ = debouncedSearch.trim().toLowerCase();

    let displayRows: DisplayRow[] = [];

    if (viewLevel === "task") {
      // Task level: use all eco rows, filtered by selected GWAs
      const data = taskData ?? [];
      displayRows = data
        .filter((t) => {
          if (selectedGwas.size === 0) return true;
          return t.gwa_title != null && selectedGwas.has(t.gwa_title);
        })
        .filter((t) => {
          if (physicalMode === "exclude") return t.physical !== true;
          if (physicalMode === "only") return t.physical === true;
          return true;
        })
        .map((t, i) => {
          const empVal = empWeighting === "freq"
            ? (geo === "nat" ? t.emp_nat_freq : t.emp_ut_freq)
            : (geo === "nat" ? t.emp_nat_value : t.emp_ut_value);
          return {
            name: t.task,
            rowId: `eco:${i}`,
            level: "dwa" as const,
            gwa: t.gwa_title ?? null,
            parent: t.iwa_title ?? null,
            gwa_title: t.gwa_title ?? null,
            iwa_title: t.iwa_title ?? null,
            dwa_title: t.dwa_title ?? null,
            emp: empVal ?? 0,
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
            physical: t.physical ?? null,
            freq_mean: t.freq_mean ?? null,
            importance: t.importance ?? null,
            relevance: t.relevance ?? null,
            sources: t.sources,
            top_mcps: t.top_mcps ?? [],
          };
        });
    } else {
      let filtered = rows.filter((r) => r.level === viewLevel);

      // GWA pill filter
      if (selectedGwas.size > 0) {
        if (viewLevel === "gwa") {
          filtered = filtered.filter((r) => selectedGwas.has(r.name));
        } else if (viewLevel === "iwa" || viewLevel === "dwa") {
          filtered = filtered.filter((r) => r.gwa != null && selectedGwas.has(r.gwa));
        }
      }

      displayRows = filtered.map((r) => waRowToDisplay(r, geo, empWeighting));

      // Physical filter on pct_physical
      if (physicalMode === "exclude") {
        displayRows = displayRows.filter((r) => r.pct_physical !== 1);
      } else if (physicalMode === "only") {
        displayRows = displayRows.filter((r) => r.pct_physical === 1 || r.pct_physical === null);
      }
    }

    // Inject pct_affected from map
    // Task-level rows are keyed by DWA title (pctAffectedMap is at DWA level when viewLevel=task)
    if (pctAffectedMap) {
      displayRows = displayRows.map((r) => ({
        ...r,
        pct_affected: viewLevel === "task"
          ? (pctAffectedMap.get(r.dwa_title ?? "") ?? null)
          : (pctAffectedMap.get(r.name) ?? null),
      }));

      // pct filter
      if (minPctAffected > 0) {
        displayRows = displayRows.filter((r) => (r.pct_affected ?? 0) >= minPctAffected);
      }
    }

    // Search filter
    if (searchQ) {
      displayRows = displayRows.filter((r) => {
        if (r.name.toLowerCase().includes(searchQ)) return true;
        if (r.title_current?.toLowerCase().includes(searchQ)) return true;
        if (r.major_occ_category?.toLowerCase().includes(searchQ)) return true;
        if (r.minor_occ_category?.toLowerCase().includes(searchQ)) return true;
        if (r.broad_occ?.toLowerCase().includes(searchQ)) return true;
        return false;
      });
    }

    // Column filters
    Object.entries(colFilters).forEach(([key, { min, max }]) => {
      const minN = min !== "" ? parseFloat(min) : null;
      const maxN = max !== "" ? parseFloat(max) : null;
      if (minN !== null || maxN !== null) {
        displayRows = displayRows.filter((r) => {
          const v = getVal(r, key);
          if (minN !== null && (v == null || v < minN)) return false;
          if (maxN !== null && (v == null || v > maxN)) return false;
          return true;
        });
      }
    });

    // Text column filters (multi-select)
    const textGetters: Record<string, (r: DisplayRow) => string | null | undefined> = {
      occ: (r) => r.title_current,
      broad_cat: (r) => r.broad_occ,
      minor_cat: (r) => r.minor_occ_category,
      major_cat: (r) => r.major_occ_category,
      dwa_col: (r) => r.dwa_title,
      iwa_col: (r) => r.iwa_title,
      gwa_col: (r) => r.gwa,
    };
    Object.entries(textColFilters).forEach(([key, vals]) => {
      if (vals.length > 0 && textGetters[key]) {
        displayRows = displayRows.filter((r) => {
          const v = textGetters[key](r) ?? "";
          return vals.includes(v);
        });
      }
    });

    // Sort
    displayRows = [...displayRows].sort((a, b) => {
      const textColMap: Record<string, (r: DisplayRow) => string | null | undefined> = {
        name: (r) => r.name,
        occ: (r) => r.title_current,
        broad_cat: (r) => r.broad_occ,
        minor_cat: (r) => r.minor_occ_category,
        major_cat: (r) => r.major_occ_category,
        dwa_col: (r) => r.dwa_title,
        iwa_col: (r) => r.iwa_title,
        gwa_col: (r) => r.gwa,
      };
      if (textColMap[sortCol]) {
        const aStr = textColMap[sortCol](a) ?? "";
        const bStr = textColMap[sortCol](b) ?? "";
        const cmp = aStr.localeCompare(bStr);
        return sortDir === "asc" ? cmp : -cmp;
      }
      const av = getVal(a, sortCol);
      const bv = getVal(b, sortCol);
      if (av == null && bv == null) return 0;
      if (av == null) return sortDir === "desc" ? 1 : -1;
      if (bv == null) return sortDir === "desc" ? -1 : 1;
      return sortDir === "desc" ? bv - av : av - bv;
    });

    return displayRows;
  }, [rows, viewLevel, selectedGwas, geo, debouncedSearch, sortCol, sortDir, colFilters, textColFilters, physicalMode, pctAffectedMap, minPctAffected, taskData, empWeighting]);

  // ── textColUniqueValues: unique sorted values per text column ─────────────
  const textColUniqueValues = useMemo(() => {
    const getters: Record<string, (r: DisplayRow) => string | null | undefined> = {
      occ: (r) => r.title_current,
      broad_cat: (r) => r.broad_occ,
      minor_cat: (r) => r.minor_occ_category,
      major_cat: (r) => r.major_occ_category,
      dwa_col: (r) => r.dwa_title,
      iwa_col: (r) => r.iwa_title,
      gwa_col: (r) => r.gwa,
    };
    const result: Record<string, string[]> = {};
    for (const [key, getter] of Object.entries(getters)) {
      const seen = new Set<string>();
      topRows.forEach((r) => { const v = getter(r); if (v) seen.add(v); });
      result[key] = Array.from(seen).sort();
    }
    return result;
  }, [topRows]);

  // ── Visible columns ────────────────────────────────────────────────────────
  const visibleCols = useMemo(() => {
    const isTaskLevel = viewLevel === "task";
    return COLUMNS.filter((c) => {
      // pct_affected, workers_aff, wages_aff are always visible (auto-computed on load)
      if (isSimple && isTaskLevel && !WA_SIMPLE_TASK_COLS.has(c.key)) return false;
      if (isSimple && !isTaskLevel && !WA_SIMPLE_COLS.has(c.key)) return false;
      if (TASK_ONLY_COLS.has(c.key) && !isTaskLevel) return false;
      if (NON_TASK_COLS.has(c.key) && viewLevel === "task") return false;
      if (hiddenCols.has(c.key)) return false;
      return true;
    });
  }, [isSimple, viewLevel, hiddenCols]);

  // ── Pre-built child row cache (avoids O(n) filtering on every render) ─────
  const childRowCache = useMemo(() => {
    const cache = new Map<string, DisplayRow[]>();
    const gwaMap = new Map<string, WAExplorerRow[]>();
    const iwaMap = new Map<string, WAExplorerRow[]>();
    rows.forEach((r) => {
      if (r.level === "iwa" && r.gwa) {
        const arr = gwaMap.get(r.gwa) ?? [];
        arr.push(r);
        gwaMap.set(r.gwa, arr);
      }
      if (r.level === "dwa" && r.parent) {
        const arr = iwaMap.get(r.parent) ?? [];
        arr.push(r);
        iwaMap.set(r.parent, arr);
      }
    });
    gwaMap.forEach((children, gwaName) => {
      cache.set(`gwa:${gwaName}`, children.map((r) => waRowToDisplay(r, geo, empWeighting)).sort((a, b) => b.emp - a.emp));
    });
    iwaMap.forEach((children, iwaName) => {
      cache.set(`iwa:${iwaName}`, children.map((r) => waRowToDisplay(r, geo, empWeighting)).sort((a, b) => b.emp - a.emp));
    });
    return cache;
  }, [rows, geo, empWeighting]);

  // ── Child row helpers ──────────────────────────────────────────────────────
  function getChildRows(parentRow: DisplayRow): DisplayRow[] {
    return childRowCache.get(`${parentRow.level}:${parentRow.name}`) ?? [];
  }

  // ── Toggle row expand ──────────────────────────────────────────────────────
  const toggleRow = useCallback((key: string, isDwa: boolean, name: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
        if (isDwa && !rowTasks[name]) {
          setRowTasks((rt) => ({ ...rt, [name]: "loading" }));
          fetchWAActivityTasks("dwa", name)
            .then((data) => setRowTasks((rt) => ({ ...rt, [name]: data.tasks })))
            .catch(() => setRowTasks((rt) => ({ ...rt, [name]: "error" })));
        }
      }
      return next;
    });
  }, [rowTasks]);

  // ── Column sort ────────────────────────────────────────────────────────────
  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(col);
      setSortDir("desc");
    }
  };

  // ── Reset ──────────────────────────────────────────────────────────────────
  const handleReset = () => {
    setViewLevel("gwa");             // Level -> GWA
    setSelectedGwas(new Set());      // GWA pills -> clear
    setSearch("");                    // Search -> clear
    setSortCol("emp");               // Sort -> emp desc
    setSortDir("desc");
    setColFilters({});               // Column filters -> clear
    setOpenFilter(null);
    setTextColFilters({});           // Text column filters -> clear
    setOpenTextFilter(null);
    setGeo("nat");                   // Geo -> nat
    setPhysicalMode("all");          // Physical -> all
    setExpandedRows(new Set());      // Expanded rows -> collapse
    setPctAffectedMap(null);         // Clear pct map (re-computed below)
    setMinPctAffected(0);            // Min pct slider -> 0
    setRowLimit(100);                // Pagination -> 100
    setEmpWeighting("freq");         // Emp weighting -> freq (Time)
    setHiddenCols(new Set());        // Hidden columns -> defaults (empty set)
    setColSelectorOpen(false);       // Close column selector
    // Re-run compute with WA simple-mode defaults by bumping generation
    setComputeGeneration((g) => g + 1);
  };

  // ── GWA pill toggle ────────────────────────────────────────────────────────
  const toggleGwa = (gwa: string) => {
    setSelectedGwas((prev) => {
      const next = new Set(prev);
      if (next.has(gwa)) {
        next.delete(gwa);
      } else {
        next.add(gwa);
      }
      return next;
    });
  };

  // ── Render a data table row (possibly expandable) ──────────────────────────
  function renderDataRow(
    row: DisplayRow,
    indent: number,
    rowKey: string,
  ): React.ReactNode {
    const isExpanded = expandedRows.has(rowKey);
    const isDwa = row.level === "dwa";
    const canExpand = row.level !== "dwa" || true; // DWA can expand to tasks
    const searchQ = search.trim().toLowerCase();

    const isTaskLevel = viewLevel === "task";
    const canExpandRow = canExpand; // task-level rows expand to show hierarchy info
    const children = isExpanded && !isDwa && !isTaskLevel ? getChildRows(row) : [];
    const tasks = isDwa && isExpanded && !isTaskLevel ? rowTasks[row.name] : undefined;

    return (
      <React.Fragment key={rowKey}>
        <tr
          onClick={canExpandRow ? () => toggleRow(rowKey, isDwa, row.name) : undefined}
          style={{
            cursor: canExpandRow ? "pointer" : "default",
            borderBottom: "1px solid var(--border-light)",
            background: indent > 0 ? `rgba(0,0,0,${indent * 0.015})` : undefined,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#f5f5f0")}
          onMouseLeave={(e) => (e.currentTarget.style.background = indent > 0 ? `rgba(0,0,0,${indent * 0.015})` : "")}
        >
          {visibleCols.map((col, ci) => {
            const isName = col.key === "name";
            return (
              <td
                key={col.key}
                style={{
                  padding: isName ? "7px 10px" : "7px 8px",
                  fontSize: 13,
                  textAlign: col.numeric ? "right" : "left",
                  verticalAlign: "middle",
                  color: "var(--text-primary)",
                  minWidth: col.width,
                  maxWidth: isName ? 400 : undefined,
                  borderRight: ci < visibleCols.length - 1 ? "1px solid var(--border-light)" : undefined,
                }}
              >
                {isName ? (
                  <div style={{
                    display: "flex", alignItems: "center",
                    gap: 5, paddingLeft: indent * 20,
                  }}>
                    <ChevronIcon open={isExpanded} />
                    {!isTaskLevel && <LevelBadge level={row.level} />}
                    <span style={{ lineHeight: 1.3 }}>
                      {highlightText(row.name, searchQ)}
                    </span>
                  </div>
                ) : (
                  renderCell(col.key, row)
                )}
              </td>
            );
          })}
        </tr>

        {/* Inline DWA task sub-table */}
        {isDwa && isExpanded && !isTaskLevel && (
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            <td colSpan={visibleCols.length} style={{ padding: 0, background: "#fafaf8" }}>
              <div style={{ paddingLeft: (indent + 1) * 20 + 10, paddingRight: 10, paddingTop: 8, paddingBottom: 12 }}>
                {tasks === "loading" && (
                  <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "8px 0" }}>Loading tasks…</p>
                )}
                {tasks === "error" && (
                  <p style={{ fontSize: 12, color: "#b91c1c", padding: "8px 0" }}>Failed to load tasks.</p>
                )}
                {Array.isArray(tasks) && tasks.length === 0 && (
                  <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "8px 0" }}>No tasks found.</p>
                )}
                {Array.isArray(tasks) && tasks.length > 0 && (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ borderCollapse: "collapse", width: "100%", tableLayout: "auto" }}>
                      <thead>
                        <WATaskSubHeader geo={geo} />
                      </thead>
                      <tbody>
                        {tasks.map((t) => (
                          <WATaskSubRow key={t.task_normalized} task={t} geo={geo} empWeighting={empWeighting} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </td>
          </tr>
        )}

        {/* Task-level expansion: show occupation + activity + task details + sources + top MCPs */}
        {isTaskLevel && isExpanded && (() => {
          const muted = { color: "var(--text-muted)" } as React.CSSProperties;
          const sources = row.sources ? Object.entries(row.sources) : [];
          const autoVals = sources.map(([, s]) => s.auto_aug).filter((v): v is number => v != null);
          const pctVals = sources.map(([, s]) => s.pct_norm).filter((v): v is number => v != null);
          const avgAuto = autoVals.length > 0 ? autoVals.reduce((a, b) => a + b, 0) / autoVals.length : null;
          const maxAuto = autoVals.length > 0 ? Math.max(...autoVals) : null;
          const avgPct = pctVals.length > 0 ? pctVals.reduce((a, b) => a + b, 0) / pctVals.length : null;
          const maxPct = pctVals.length > 0 ? Math.max(...pctVals) : null;
          const topMcps = row.top_mcps ?? [];
          return (
            <tr style={{ background: "#f7f7f5", borderBottom: "1px solid var(--border)" }}>
              <td colSpan={visibleCols.length} style={{ padding: "10px 20px 14px 28px" }}>
                <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                  {/* Occupation Categories */}
                  {(row.title_current || row.broad_occ || row.minor_occ_category || row.major_occ_category) && (
                    <div style={{ minWidth: 200 }}>
                      <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Occupation Categories</p>
                      {row.title_current && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Occ:</b> {row.title_current}</p>}
                      {row.broad_occ && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Broad:</b> {row.broad_occ}</p>}
                      {row.minor_occ_category && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>Minor:</b> {row.minor_occ_category}</p>}
                      {row.major_occ_category && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>Major:</b> {row.major_occ_category}</p>}
                    </div>
                  )}
                  {/* Activity Classification */}
                  {(row.gwa_title || row.iwa_title || row.dwa_title) && (
                    <div style={{ minWidth: 200 }}>
                      <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Work Activities</p>
                      {row.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {row.gwa_title}</p>}
                      {row.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {row.iwa_title}</p>}
                      {row.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {row.dwa_title}</p>}
                    </div>
                  )}
                  {/* Task Detail */}
                  <div>
                    <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Task Detail</p>
                    <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                      <tbody>
                        <tr>
                          <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Emp</td>
                          <td style={{ padding: "2px 0" }}>{fmtEmp(row.emp)}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Wage</td>
                          <td style={{ padding: "2px 0" }}>{fmtWage(row.wage)}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Physical</td>
                          <td style={{ padding: "2px 0" }}>
                            {row.pct_physical === 1 ? <span style={{ color: "#16a34a" }}>✓ Yes</span> : row.pct_physical === 0 ? <span style={muted}>✗ No</span> : <span style={muted}>—</span>}
                          </td>
                        </tr>
                        <tr>
                          <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Freq</td>
                          <td style={{ padding: "2px 0" }}>{row.freq_mean != null ? row.freq_mean.toFixed(2) : <span style={muted}>—</span>}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Imp</td>
                          <td style={{ padding: "2px 0" }}>{row.importance != null ? row.importance.toFixed(2) : <span style={muted}>—</span>}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: "2px 8px 2px 0", color: "var(--text-muted)", fontWeight: 600 }}>Rel</td>
                          <td style={{ padding: "2px 0" }}>{row.relevance != null ? row.relevance.toFixed(2) : <span style={muted}>—</span>}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  {/* Source Breakdown */}
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
                              <td style={{ padding: "2px 8px", textAlign: "right" }}>{stats.auto_aug != null ? stats.auto_aug.toFixed(3) : <span style={muted}>—</span>}</td>
                              <td style={{ padding: "2px 8px", textAlign: "right" }}>{stats.pct_norm != null ? fmtPctNorm(stats.pct_norm) : <span style={muted}>—</span>}</td>
                            </tr>
                          ))}
                          <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                            <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                              <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--brand-light)", border: "1px solid var(--brand)", color: "var(--brand)", fontWeight: 700 }}>AVG</span>
                            </td>
                            <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>
                              {avgAuto != null ? avgAuto.toFixed(3) : <span style={muted}>—</span>}
                            </td>
                            <td style={{ padding: "4px 8px 2px", textAlign: "right", fontWeight: 700 }}>
                              {avgPct != null ? fmtPctNorm(avgPct) : <span style={muted}>—</span>}
                            </td>
                          </tr>
                          <tr>
                            <td style={{ padding: "2px 10px 4px 0", fontWeight: 700 }}>
                              <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "#fffbeb", border: "1px solid #d97706", color: "#d97706", fontWeight: 700 }}>MAX</span>
                            </td>
                            <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>
                              {maxAuto != null ? maxAuto.toFixed(3) : <span style={muted}>—</span>}
                            </td>
                            <td style={{ padding: "2px 8px 4px", textAlign: "right", fontWeight: 700 }}>
                              {maxPct != null ? fmtPctNorm(maxPct) : <span style={muted}>—</span>}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  )}
                  {/* Top MCP Servers */}
                  {topMcps.length > 0 && (
                    <div style={{ minWidth: 200 }}>
                      <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Top MCP Servers</p>
                      <ol style={{ margin: 0, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 3 }}>
                        {topMcps.slice(0, 5).map((mcp, i) => (
                          <li key={i} style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                            {mcp.url
                              ? <a href={mcp.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand)", textDecoration: "none" }}>{mcp.title}</a>
                              : <span>{mcp.title}</span>}
                            {mcp.rating != null && <span style={{ color: "var(--text-muted)", marginLeft: 4 }}>({mcp.rating.toFixed(1)})</span>}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              </td>
            </tr>
          );
        })()}

        {/* Inline IWA/GWA child rows */}
        {!isDwa && !isTaskLevel && isExpanded && children.map((child, ci) => {
          const childKey = `${rowKey}__${child.name}__${ci}`;
          return renderDataRow(child, indent + 1, childKey);
        })}
      </React.Fragment>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{
      height: "calc(100vh - var(--nav-height, 56px))",
      display: "flex", flexDirection: "column",
      background: "var(--bg-base)",
      overflow: "hidden",
    }}>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        padding: "12px 20px 10px",
        flexShrink: 0,
        display: "flex", flexDirection: "column", gap: 8,
      }}>
        {/* Row 1: title + count */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
            Work Activities Explorer
          </h1>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {topRows.length.toLocaleString()} {viewLevel.toUpperCase()} rows
          </span>
        </div>

        {/* Row 2: GWA pills */}
        <div style={{
          display: "flex", flexWrap: "nowrap", gap: 5,
          overflowX: "auto", paddingBottom: 4,
        }}>
          <button
            onClick={() => setSelectedGwas(new Set())}
            style={{
              fontSize: 11, padding: "3px 9px", borderRadius: 14,
              border: `1.5px solid ${selectedGwas.size === 0 ? "var(--brand)" : "var(--border)"}`,
              background: selectedGwas.size === 0 ? "var(--brand-light)" : "transparent",
              color: selectedGwas.size === 0 ? "var(--brand)" : "var(--text-secondary)",
              fontWeight: selectedGwas.size === 0 ? 600 : 400,
              cursor: "pointer",
            }}
          >All</button>
          {allGwas.map((gwa) => {
            const sel = selectedGwas.has(gwa);
            return (
              <button
                key={gwa}
                onClick={() => toggleGwa(gwa)}
                style={{
                  fontSize: 11, padding: "3px 9px", borderRadius: 14,
                  border: `1.5px solid ${sel ? "var(--brand)" : "var(--border)"}`,
                  background: sel ? "var(--brand-light)" : "transparent",
                  color: sel ? "var(--brand)" : "var(--text-secondary)",
                  fontWeight: sel ? 600 : 400,
                  cursor: "pointer",
                  whiteSpace: "nowrap", flexShrink: 0,
                }}
              >{gwa}</button>
            );
          })}
        </div>

        {/* Row 3: controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>Level:</span>
            <BtnSeg<WALevel>
              opts={[{ v: "gwa", l: "GWA" }, { v: "iwa", l: "IWA" }, { v: "dwa", l: "DWA" }, { v: "task", l: "Task" }]}
              val={viewLevel}
              onChange={(v) => {
                setViewLevel(v);
                setExpandedRows(new Set());
              }}
            />
          </div>

          <input
            type="text"
            placeholder="Search…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              fontSize: 12, padding: "4px 10px", borderRadius: 5,
              border: "1px solid var(--border)", outline: "none",
              color: "var(--text-primary)", background: "var(--bg-surface)",
              minWidth: 180,
            }}
          />

          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>Geo:</span>
            <BtnSeg<"nat" | "ut">
              opts={[{ v: "nat", l: "Nat" }, { v: "ut", l: "Utah" }]}
              val={geo}
              onChange={setGeo}
            />
          </div>

          {!isSimple && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>Phys:</span>
            <BtnSeg<"all" | "exclude" | "only">
              opts={[{ v: "all", l: "All" }, { v: "exclude", l: "No Phys" }, { v: "only", l: "Phys Only" }]}
              val={physicalMode}
              onChange={setPhysicalMode}
            />
          </div>
          )}

          {!isSimple && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>Emp Weight:</span>
            <BtnSeg<"freq" | "value">
              opts={[{ v: "freq", l: "Time" }, { v: "value", l: "Value" }]}
              val={empWeighting}
              onChange={setEmpWeighting}
            />
          </div>
          )}

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
                if (TASK_ONLY_COLS.has(c.key) && viewLevel !== "task") return false;
                if (NON_TASK_COLS.has(c.key) && viewLevel === "task") return false;
                if (isSimple && viewLevel === "task" && !WA_SIMPLE_TASK_COLS.has(c.key)) return false;
                if (isSimple && viewLevel !== "task" && !WA_SIMPLE_COLS.has(c.key)) return false;
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
                  {viewLevel === "task" && (
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
                        {viewLevel === "task" && TASK_LABEL_OVERRIDES[c.key] ? TASK_LABEL_OVERRIDES[c.key] : c.label}
                      </label>
                    );
                  })}
                </div>
              );
            })()}
          </div>

          <button
            onClick={handleReset}
            style={{
              fontSize: 11, padding: "4px 12px", borderRadius: 5,
              border: "1px solid var(--border)", background: "transparent",
              color: "var(--text-secondary)", cursor: "pointer",
            }}
          >Reset</button>
        </div>

        {/* Row 4: % Tasks Affected panel (hidden in simple mode — auto-computed) */}
        {!isSimple && (
          <WaPctComputePanel config={config} geo={geo} viewLevel={viewLevel} onResult={setPctAffectedMap} empWeighting={empWeighting} />
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

      {/* ── Table ──────────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowX: "auto", overflowY: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{
              position: "sticky", top: 0,
              background: "var(--bg-surface)", zIndex: 10,
              borderBottom: "2px solid var(--border)",
            }}>
              {visibleCols.map((col) => {
                const isSorted = sortCol === col.key;
                const hasNumFilter = !!(colFilters[col.key]?.min || colFilters[col.key]?.max);
                const isTextCol = TEXT_FILTER_COLS.has(col.key);
                const hasTextFilter = isTextCol && (textColFilters[col.key]?.length ?? 0) > 0;
                return (
                  <th
                    key={col.key}
                    style={{
                      padding: "7px 8px",
                      textAlign: (col.key === "name" || isTextCol) ? "left" : "right",
                      fontSize: 11, fontWeight: 700,
                      color: isSorted ? "var(--brand)" : "var(--text-muted)",
                      textTransform: "uppercase", letterSpacing: "0.06em",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      width: col.width,
                      cursor: "pointer",
                      userSelect: "none",
                      position: "relative",
                    }}
                    onClick={() => handleSort(col.key)}
                  >
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 3, paddingRight: (col.numeric || isTextCol) ? 14 : 0 }}>
                      {viewLevel === "task" && TASK_LABEL_OVERRIDES[col.key] ? TASK_LABEL_OVERRIDES[col.key] : col.label}
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
                          setOpenFilter((prev) => (prev === col.key ? null : col.key));
                          setOpenTextFilter(null);
                        }}
                        style={{
                          position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)",
                          cursor: "pointer",
                          color: hasNumFilter ? "var(--brand)" : "var(--text-muted)",
                          opacity: hasNumFilter ? 1 : 0.5,
                          display: "inline-flex",
                        }}
                        title="Filter"
                      >
                        <FunnelIcon />
                      </span>
                    )}
                    {isTextCol && (
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenTextFilter((prev) => (prev === col.key ? null : col.key));
                          setOpenFilter(null);
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
                    )}
                    {openFilter === col.key && (
                      <ColumnFilterDropdown
                        colKey={col.key}
                        filters={colFilters}
                        setFilters={setColFilters}
                        onClose={() => setOpenFilter(null)}
                      />
                    )}
                    {openTextFilter === col.key && (
                      <TextColumnFilterDropdown
                        colKey={col.key}
                        values={textColUniqueValues[col.key] ?? []}
                        selected={textColFilters[col.key] ?? []}
                        setFilters={setTextColFilters}
                        onClose={() => setOpenTextFilter(null)}
                      />
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {/* Task level loading */}
            {viewLevel === "task" && taskLoading && (
              <tr>
                <td colSpan={visibleCols.length} style={{ padding: "40px", textAlign: "center" }}>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 20, height: 20, borderRadius: "50%", border: "2px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
                    <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading tasks…</span>
                  </div>
                </td>
              </tr>
            )}
            {!taskLoading && topRows.length === 0 && (
              <tr>
                <td colSpan={visibleCols.length} style={{
                  padding: "40px 20px", textAlign: "center",
                  fontSize: 13, color: "var(--text-muted)",
                }}>
                  No rows match the current filters.
                </td>
              </tr>
            )}
            {!taskLoading && topRows.slice(0, rowLimit).map((row, i) => renderDataRow(row, 0, row.rowId ? `${viewLevel}__${row.rowId}` : `${viewLevel}__${row.name}__${i}`))}
          </tbody>
        </table>

        {/* Pagination footer */}
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
    </div>
  );
}
