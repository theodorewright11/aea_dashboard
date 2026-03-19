"use client";

import React, { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import type {
  OccupationSummary,
  TaskDetail,
  OccupationTasksResponse,
  ConfigResponse,
  ChartRow,
  ExplorerGroupRow,
  ExplorerGroupsResponse,
  AllTaskRow,
} from "@/lib/types";
import { fetchOccupationTasks, fetchCompute, fetchAllTasks } from "@/lib/api";

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
  { key: "emp",          label: "Emp",              width: 90,  numeric: true,  tooltip: "Total employment (BLS OEWS 2024)" },
  { key: "wage",         label: "Med Wage",         width: 90,  numeric: true,  tooltip: "Median annual wage (BLS OEWS 2024)" },
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
  { key: "pct_affected",  label: "% Tasks Aff.",     width: 100, numeric: true,  tooltip: "% Tasks Affected from the compute panel. Uses the selected datasets and method." },
  { key: "workers_aff",   label: "Workers Aff.",     width: 110, numeric: true,  tooltip: "Workers affected = % Tasks Affected × employment. Requires compute panel result." },
  { key: "wages_aff",     label: "Wages Aff. ($B)",  width: 120, numeric: true,  tooltip: "Wages affected (billions) = % Tasks Affected × employment × median wage. Requires compute panel result." },
];

// ── FlatRow model ──────────────────────────────────────────────────────────────

interface FlatRow {
  name: string;
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

function taskToRow(t: AllTaskRow): FlatRow {
  return {
    name: t.task,
    emp: 0,
    wage: null,
    n_occs: t.n_occs,
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
  };
}

// ── Column value getter ────────────────────────────────────────────────────────

function getVal(row: FlatRow, col: string, pctMap: Map<string, number> | null): number | null {
  switch (col) {
    case "emp":          return row.emp;
    case "wage":         return row.wage;
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
    case "pct_affected": return pctMap?.get(row.name) ?? null;
    case "workers_aff": {
      const pct = pctMap?.get(row.name);
      return pct != null ? (pct / 100) * row.emp : null;
    }
    case "wages_aff": {
      const pct = pctMap?.get(row.name);
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
  switch (col) {
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
    case "pct_affected": {
      const v = pctMap?.get(row.name) ?? null;
      return v != null
        ? <span style={{ color: "var(--brand)", fontWeight: 500 }}>{v.toFixed(2)}%</span>
        : <span style={muted}>—</span>;
    }
    case "workers_aff": {
      const pct = pctMap?.get(row.name);
      if (pct == null) return <span style={muted}>—</span>;
      const v = (pct / 100) * row.emp;
      return <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtEmp(v)}</span>;
    }
    case "wages_aff": {
      const pct = pctMap?.get(row.name);
      if (pct == null || row.wage == null) return <span style={muted}>—</span>;
      const v = (pct / 100) * row.emp * row.wage / 1e9;
      return <span style={{ color: "var(--brand)", fontWeight: 500 }}>${v.toFixed(2)}B</span>;
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
}: {
  task: TaskDetail;
  physicalMode: "all" | "exclude" | "only";
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
              {(task.gwa_title || task.iwa_title || task.dwa_title) && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>Activity Classification</p>
                  {task.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {task.gwa_title}</p>}
                  {task.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {task.iwa_title}</p>}
                  {task.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {task.dwa_title}</p>}
                </div>
              )}
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
  useAdjMean: boolean;
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
    useAdjMean: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [computed, setComputed] = useState(false);

  useEffect(() => { setSettings((s) => ({ ...s, geo })); }, [geo]);

  function set<K extends keyof PctSettings>(k: K, v: PctSettings[K]) {
    setSettings((s) => ({ ...s, [k]: v }));
  }

  const hasMCP = settings.datasets.some((d) => d.startsWith("MCP"));

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
        useAdjMean: settings.useAutoAug && settings.useAdjMean,
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
                      const next = sel ? settings.datasets.filter((d) => d !== ds) : [...settings.datasets, ds];
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
                <BtnSeg opts={[{ v: "freq", l: "Freq" }, { v: "imp", l: "Imp" }]} val={settings.method} onChange={(v) => set("method", v)} />
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

export default function ExplorerView({ occupations, groups, config }: Props) {
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
  const [taskData, setTaskData] = useState<AllTaskRow[] | null>(null);
  const [taskLoading, setTaskLoading] = useState(false);
  const [taskPage, setTaskPage] = useState(100);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [rowTasks, setRowTasks] = useState<Record<string, TaskDetail[] | "loading" | "error">>({});
  const [minEmp, setMinEmp] = useState("");
  const [minWage, setMinWage] = useState("");

  // ── Load task data when task level selected ──────────────────────────────
  useEffect(() => {
    if (tableLevel === "task" && taskData === null && !taskLoading) {
      setTaskLoading(true);
      fetchAllTasks()
        .then((res) => setTaskData(res.tasks))
        .catch(() => setTaskData([]))
        .finally(() => setTaskLoading(false));
    }
  }, [tableLevel, taskData, taskLoading]);

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
    const searchQ = search.trim().toLowerCase();

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
      const data = taskData ?? [];
      rows = data.map(taskToRow);
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

    // Emp/wage filter
    const empMin = parseFloat(minEmp);
    const wageMin = parseFloat(minWage);
    if (!isNaN(empMin) && empMin > 0) rows = rows.filter((r) => r.emp >= empMin);
    if (!isNaN(wageMin) && wageMin > 0) rows = rows.filter((r) => r.wage != null && r.wage >= wageMin);

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

    // Search
    if (searchQ) {
      if (effectiveLevel === tableLevel || searchLevel === "all") {
        rows = rows.filter((r) => r.name.toLowerCase().includes(searchQ));
      }
    }

    // Sort
    rows = [...rows].sort((a, b) => {
      if (sortCol === "name") {
        const cmp = a.name.localeCompare(b.name);
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
    tableLevel, groups, occupations, taskData, geo, selectedMajors, search, searchLevel,
    sortCol, sortDir, colFilters, physicalMode, pctAffectedMap, minPctAffected, minEmp, minWage,
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
    setSelectedMajors(new Set());
    setSearch("");
    setSearchLevel("all");
    setSortCol("emp");
    setSortDir("desc");
    setColFilters({});
    setPhysicalMode("all");
    setPctAffectedMap(null);
    setMinPctAffected(0);
    setTableLevel("major");
    setMinEmp("");
    setMinWage("");
    setExpandedRows(new Set());
  };

  // ── Visible columns (hide pct_affected when no map, hide n_occs at occ/task level) ──
  const visibleCols = useMemo(() => {
    return COLUMNS.filter((c) => {
      if ((c.key === "pct_affected" || c.key === "workers_aff" || c.key === "wages_aff") && !pctAffectedMap) return false;
      return true;
    });
  }, [pctAffectedMap]);

  // ── Total count for header ────────────────────────────────────────────────
  const totalOccs = occupations.length;
  const totalTasks = taskData?.length ?? null;

  // ── Build child rows for drilldown ────────────────────────────────────────
  function buildChildRows(row: FlatRow, currentLevel: TableLevel): FlatRow[] {
    if (currentLevel === "task" || currentLevel === "occupation") return [];
    if (currentLevel === "major") {
      // children are minor rows with parent === row.name
      return (groups.minor ?? [])
        .filter((g) => g.parent === row.name)
        .map((g) => groupToRow(g, geo))
        .sort((a, b) => b.emp - a.emp);
    }
    if (currentLevel === "minor") {
      return (groups.broad ?? [])
        .filter((g) => g.parent === row.name)
        .map((g) => groupToRow(g, geo))
        .sort((a, b) => b.emp - a.emp);
    }
    if (currentLevel === "broad") {
      return occupations
        .filter((o) => o.broad === row.name)
        .map((o) => occToRow(o, geo))
        .sort((a, b) => b.emp - a.emp);
    }
    return [];
  }

  function childLevel(level: TableLevel): TableLevel {
    if (level === "major") return "minor";
    if (level === "minor") return "broad";
    if (level === "broad") return "occupation";
    return "task";
  }

  // ── Render a single table row (recursive) ────────────────────────────────
  function renderRow(row: FlatRow, level: TableLevel, indent: number): React.ReactNode {
    const rowKey = `${level}:${row.name}`;
    const isExpanded = expandedRows.has(rowKey);
    const isOcc = level === "occupation" || row.isOcc === true;
    const isTask = level === "task";
    const canExpand = !isTask;
    const indentPx = indent * 20;

    const taskState = isOcc ? rowTasks[row.name] : undefined;

    const childRowsData = (isExpanded && !isOcc && !isTask)
      ? buildChildRows(row, level)
      : [];
    const nextLvl = childLevel(level);

    return (
      <React.Fragment key={rowKey}>
        <tr
          onClick={canExpand ? () => toggleRow(rowKey, isOcc, row.name) : undefined}
          style={{
            cursor: canExpand ? "pointer" : "default",
            borderBottom: "1px solid var(--border-light)",
          }}
          onMouseEnter={(e) => { if (canExpand) e.currentTarget.style.background = "#f9f9f7"; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
        >
          {visibleCols.map((col, ci) => {
            const isName = col.key === "name";
            const isNum = col.numeric;
            return (
              <td
                key={col.key}
                style={{
                  padding: "7px 8px",
                  paddingLeft: isName ? 8 + indentPx : 8,
                  fontSize: 13,
                  color: "var(--text-primary)",
                  textAlign: isName ? "left" : "right",
                  whiteSpace: isName ? "normal" : "nowrap",
                  verticalAlign: "top",
                  minWidth: ci === 0 ? col.width + indentPx : undefined,
                  width: ci === 0 ? undefined : col.width,
                  fontWeight: indent === 0 ? 500 : 400,
                }}
              >
                {isName ? (
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 5 }}>
                    {canExpand && <span style={{ marginTop: 1, flexShrink: 0 }}><ChevronIcon open={isExpanded} /></span>}
                    {!canExpand && <span style={{ width: 11, flexShrink: 0 }} />}
                    <span style={{ lineHeight: 1.4 }}>
                      {search.trim() ? highlightText(row.name, search.trim()) : row.name}
                    </span>
                  </div>
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
                        <TaskSubRow key={t.task_normalized} task={t} physicalMode={physicalMode} />
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

        {/* Recursive child rows */}
        {isExpanded && !isOcc && !isTask && childRowsData.map((child) =>
          renderRow(child, nextLvl, indent + 1)
        )}
      </React.Fragment>
    );
  }

  // ── Task level rows with pagination ──────────────────────────────────────
  const shownTaskRows = tableLevel === "task" ? topRows.slice(0, taskPage) : topRows;

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
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {/* Reset */}
          <button
            onClick={handleReset}
            style={{
              fontSize: 11, padding: "4px 10px", border: "1px solid var(--border)",
              borderRadius: 5, background: "transparent", cursor: "pointer",
              color: "var(--text-secondary)",
            }}
          >Reset</button>
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
          {/* Physical */}
          <BtnSeg
            opts={[{ v: "all", l: "All" }, { v: "exclude", l: "No Phys" }, { v: "only", l: "Phys only" }]}
            val={physicalMode}
            onChange={setPhysicalMode}
          />

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

          {/* Min Emp / Min Wage inputs */}
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Min Emp:</span>
            <input
              type="number"
              value={minEmp}
              onChange={(e) => setMinEmp(e.target.value)}
              placeholder="0"
              style={{
                width: 80, fontSize: 11, padding: "4px 6px",
                border: "1px solid var(--border)", borderRadius: 4,
                outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)",
              }}
            />
          </div>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Min Wage:</span>
            <input
              type="number"
              value={minWage}
              onChange={(e) => setMinWage(e.target.value)}
              placeholder="0"
              style={{
                width: 80, fontSize: 11, padding: "4px 6px",
                border: "1px solid var(--border)", borderRadius: 4,
                outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)",
              }}
            />
          </div>

          {/* Showing count */}
          <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: "auto" }}>
            {topRows.length} rows
          </span>
        </div>

        {/* Row 3: PctComputePanel */}
        <PctComputePanel config={config} geo={geo} tableLevel={tableLevel} onResult={setPctAffectedMap} />

        {/* % Tasks Affected slider (shown when map computed) */}
        {pctAffectedMap && (
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
                      textAlign: col.key === "name" ? "left" : "right",
                      fontSize: 11,
                      fontWeight: 700,
                      color: isSorted ? "var(--brand)" : "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.06em",
                      whiteSpace: "nowrap",
                      width: col.width,
                      cursor: "pointer",
                      userSelect: "none",
                      position: "relative",
                    }}
                    onClick={() => handleSort(col.key)}
                  >
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
                      {col.label}
                      {col.tooltip && <InfoTooltip text={col.tooltip} />}
                      {isSorted && (
                        <span style={{ color: "var(--brand)", fontSize: 10 }}>
                          {sortDir === "desc" ? "↓" : "↑"}
                        </span>
                      )}
                      {col.numeric && (
                        <span
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenFilter((prev) => prev === col.key ? null : col.key);
                          }}
                          style={{
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
                    </div>
                    {openFilter === col.key && (
                      <ColumnFilterDropdown
                        colKey={col.key}
                        filters={colFilters}
                        setFilters={setColFilters}
                        onClose={() => setOpenFilter(null)}
                      />
                    )}
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
            {!taskLoading && (tableLevel === "task" ? shownTaskRows : topRows).map((row) =>
              renderRow(row, tableLevel, 0)
            )}
          </tbody>
        </table>

        {/* Task pagination */}
        {tableLevel === "task" && !taskLoading && topRows.length > taskPage && (
          <div style={{ padding: "14px 20px", textAlign: "center", borderTop: "1px solid var(--border-light)" }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)", marginRight: 12 }}>
              Showing {Math.min(taskPage, topRows.length)} of {topRows.length} tasks.
            </span>
            <button
              onClick={() => setTaskPage((p) => p + 100)}
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
