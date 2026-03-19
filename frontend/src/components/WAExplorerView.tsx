"use client";

import React, {
  useState,
  useMemo,
  useCallback,
  useEffect,
  useRef,
} from "react";
import { createPortal } from "react-dom";
import type { WAExplorerRow, WATaskDetail } from "@/lib/types";
import { fetchWAActivityTasks } from "@/lib/api";

// ── Props ──────────────────────────────────────────────────────────────────────

interface Props {
  rows: WAExplorerRow[];
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
  if (v < 0.00001) return `${v}%`;
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
  { key: "name",         label: "Name",            width: 300, numeric: false },
  { key: "emp",          label: "Emp",              width: 90,  numeric: true,  tooltip: "Total employment (BLS OEWS 2024) across occupations in this activity" },
  { key: "wage",         label: "Med Wage",         width: 90,  numeric: true,  tooltip: "Employment-weighted median annual wage" },
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
];

// ── Display row model ──────────────────────────────────────────────────────────

interface DisplayRow {
  name: string;
  level: "gwa" | "iwa" | "dwa";
  gwa: string | null;
  parent: string | null;
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
}

function waRowToDisplay(row: WAExplorerRow, geo: "nat" | "ut"): DisplayRow {
  return {
    name: row.name,
    level: row.level,
    gwa: row.gwa ?? null,
    parent: row.parent ?? null,
    emp: (geo === "nat" ? row.emp_nat : row.emp_ut) ?? 0,
    wage: (geo === "nat" ? row.wage_nat : row.wage_ut) ?? null,
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
    case "emp":          return fmtEmp(row.emp);
    case "wage":         return fmtWage(row.wage);
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

function SortIcon({ col, sortCol, sortDir }: { col: string; sortCol: string; sortDir: "asc" | "desc" }) {
  if (col !== sortCol) {
    return (
      <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="2" style={{ color: "var(--text-muted)", opacity: 0.4, flexShrink: 0 }}>
        <polyline points="6 9 12 15 18 9" />
      </svg>
    );
  }
  return (
    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2.5" style={{ color: "var(--brand)", flexShrink: 0, transform: sortDir === "asc" ? "rotate(180deg)" : undefined }}>
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function FunnelIcon({ active }: { active?: boolean }) {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      style={{ color: active ? "var(--brand)" : "var(--text-muted)" }} aria-hidden="true">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  );
}

// ── Portal-based InfoTooltip ───────────────────────────────────────────────────

function InfoTooltip({ text }: { text: string }) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);

  const handleMove = (e: React.MouseEvent) => {
    setPos({ x: e.clientX + 12, y: e.clientY + 14 });
  };

  return (
    <span style={{ position: "relative", display: "inline-flex", alignItems: "center", marginLeft: 3 }}>
      <span
        onMouseEnter={(e) => setPos({ x: e.clientX + 12, y: e.clientY + 14 })}
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
          borderRadius: 6, maxWidth: 300, zIndex: 9999, pointerEvents: "none",
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

// ── Task sub-table for expanded DWA rows ───────────────────────────────────────

function WATaskSubRow({ task, geo }: { task: WATaskDetail; geo: "nat" | "ut" }) {
  const [expanded, setExpanded] = useState(false);

  const avgAuto = task.avg_auto_aug;
  const maxAuto = task.max_auto_aug;
  const avgPct  = task.avg_pct_norm;
  const maxPct  = task.max_pct_norm;
  const barPct  = avgAuto != null ? Math.min(avgAuto / 5, 1) * 100 : null;
  const emp     = geo === "nat" ? task.emp_nat : task.emp_ut;
  const sources = Object.entries(task.sources ?? {});

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "6px 10px", fontSize: 11, color: "var(--text-primary)", verticalAlign: "top" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 5 }}>
            <ChevronIcon open={expanded} />
            <span style={{ lineHeight: 1.4 }}>{task.task}</span>
          </div>
        </td>
        <td style={{ padding: "6px 6px", textAlign: "center", verticalAlign: "top", width: 44 }}>
          {task.physical === true
            ? <span style={{ color: "#16a34a", fontSize: 11 }}>✓</span>
            : task.physical === false
            ? <span style={{ color: "var(--text-muted)", fontSize: 11 }}>✗</span>
            : <span style={{ color: "var(--text-muted)", fontSize: 10 }}>—</span>}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 80, verticalAlign: "top" }}>
          {fmtEmp(emp)}
        </td>
        <td style={{ padding: "6px 6px", fontSize: 11, color: "var(--text-secondary)", textAlign: "right", width: 80, verticalAlign: "top" }}>
          {fmtWage(task.wage_nat)}
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
          <td colSpan={8} style={{ padding: "10px 20px 14px 28px" }}>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              {(task.gwa_title || task.iwa_title || task.dwa_title) && (
                <div style={{ minWidth: 200 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 }}>
                    Activity Classification
                  </p>
                  {task.gwa_title && (
                    <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}>
                      <b>GWA:</b> {task.gwa_title}
                    </p>
                  )}
                  {task.iwa_title && (
                    <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}>
                      <b>IWA:</b> {task.iwa_title}
                    </p>
                  )}
                  {task.dwa_title && (
                    <p style={{ fontSize: 11, color: "var(--text-secondary)" }}>
                      <b>DWA:</b> {task.dwa_title}
                    </p>
                  )}
                </div>
              )}
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
                            <span style={{
                              fontSize: 10, padding: "1px 5px", borderRadius: 4,
                              background: "var(--bg-sidebar)", border: "1px solid var(--border)",
                              color: "var(--text-secondary)",
                            }}>{src}</span>
                          </td>
                          <td style={{ padding: "2px 8px", textAlign: "right" }}>
                            {stats.auto_aug != null
                              ? stats.auto_aug.toFixed(3)
                              : <span style={{ color: "var(--text-muted)" }}>—</span>}
                          </td>
                          <td style={{ padding: "2px 8px", textAlign: "right" }}>
                            {stats.pct_norm != null
                              ? fmtPctNorm(stats.pct_norm)
                              : <span style={{ color: "var(--text-muted)" }}>—</span>}
                          </td>
                        </tr>
                      ))}
                      <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                        <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                          <span style={{
                            fontSize: 10, padding: "1px 5px", borderRadius: 4,
                            background: "var(--brand-light)", border: "1px solid var(--brand)",
                            color: "var(--brand)", fontWeight: 700,
                          }}>AVG</span>
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
                          <span style={{
                            fontSize: 10, padding: "1px 5px", borderRadius: 4,
                            background: "#fffbeb", border: "1px solid #d97706",
                            color: "#d97706", fontWeight: 700,
                          }}>MAX</span>
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

function WATaskSubHeader({ geo }: { geo: "nat" | "ut" }) {
  return (
    <tr style={{ borderBottom: "2px solid var(--border)" }}>
      <th style={{ padding: "5px 10px 5px", textAlign: "left", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Task</th>
      <th style={{ padding: "5px 6px", textAlign: "center", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 44 }}>Phys</th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Emp {geo === "ut" ? "(UT)" : "(Nat)"}
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Med Wage
      </th>
      <th style={{ padding: "5px 6px", textAlign: "left", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 100, whiteSpace: "nowrap" }}>
        Auto Avg<InfoTooltip text="Avg auto-aug (0–5) across sources" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 72, whiteSpace: "nowrap" }}>
        Auto Max
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
        Pct Avg<InfoTooltip text="Avg pct (share of AI conversations)" />
      </th>
      <th style={{ padding: "5px 6px", textAlign: "right", fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", width: 80, whiteSpace: "nowrap" }}>
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

type WALevel = "gwa" | "iwa" | "dwa";
type SortDir = "asc" | "desc";

// ── Main WAExplorerView ────────────────────────────────────────────────────────

export default function WAExplorerView({ rows }: Props) {
  // ── State ──────────────────────────────────────────────────────────────────
  const [viewLevel, setViewLevel]   = useState<WALevel>("gwa");
  const [selectedGwas, setSelectedGwas] = useState<Set<string>>(new Set());
  const [search, setSearch]         = useState("");
  const [sortCol, setSortCol]       = useState<string>("emp");
  const [sortDir, setSortDir]       = useState<SortDir>("desc");
  const [colFilters, setColFilters] = useState<Record<string, { min: string; max: string }>>({});
  const [openFilter, setOpenFilter] = useState<string | null>(null);
  const [geo, setGeo]               = useState<"nat" | "ut">("nat");
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [rowTasks, setRowTasks]     = useState<Record<string, WATaskDetail[] | "loading" | "error">>({});

  // ── Derived: GWA pill names ────────────────────────────────────────────────
  const allGwas = useMemo(() => {
    return Array.from(new Set(rows.filter((r) => r.level === "gwa").map((r) => r.name))).sort();
  }, [rows]);

  // ── Build top-level display rows ───────────────────────────────────────────
  const topRows = useMemo<DisplayRow[]>(() => {
    const searchQ = search.trim().toLowerCase();

    let filtered = rows.filter((r) => r.level === viewLevel);

    // GWA pill filter
    if (selectedGwas.size > 0) {
      if (viewLevel === "gwa") {
        filtered = filtered.filter((r) => selectedGwas.has(r.name));
      } else if (viewLevel === "iwa") {
        // For IWA rows the gwa field stores the parent GWA name
        filtered = filtered.filter((r) => r.gwa != null && selectedGwas.has(r.gwa));
      } else if (viewLevel === "dwa") {
        // For DWA rows the gwa field also stores the GWA ancestor
        filtered = filtered.filter((r) => r.gwa != null && selectedGwas.has(r.gwa));
      }
    }

    let displayRows = filtered.map((r) => waRowToDisplay(r, geo));

    // Search filter
    if (searchQ) {
      displayRows = displayRows.filter((r) => r.name.toLowerCase().includes(searchQ));
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

    // Sort
    displayRows = [...displayRows].sort((a, b) => {
      if (sortCol === "name") {
        const cmp = a.name.localeCompare(b.name);
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
  }, [rows, viewLevel, selectedGwas, geo, search, sortCol, sortDir, colFilters]);

  // ── Child row helpers ──────────────────────────────────────────────────────
  function getChildRows(parentRow: DisplayRow): DisplayRow[] {
    if (parentRow.level === "gwa") {
      // Children are IWA rows where gwa === parentRow.name
      return rows
        .filter((r) => r.level === "iwa" && r.gwa === parentRow.name)
        .map((r) => waRowToDisplay(r, geo))
        .sort((a, b) => b.emp - a.emp);
    }
    if (parentRow.level === "iwa") {
      // Children are DWA rows where parent === parentRow.name
      return rows
        .filter((r) => r.level === "dwa" && r.parent === parentRow.name)
        .map((r) => waRowToDisplay(r, geo))
        .sort((a, b) => b.emp - a.emp);
    }
    return [];
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
    setViewLevel("gwa");
    setSelectedGwas(new Set());
    setSearch("");
    setSortCol("emp");
    setSortDir("desc");
    setColFilters({});
    setOpenFilter(null);
    setGeo("nat");
    setExpandedRows(new Set());
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

    const children = isExpanded && !isDwa ? getChildRows(row) : [];
    const tasks = isDwa && isExpanded ? rowTasks[row.name] : undefined;

    return (
      <React.Fragment key={rowKey}>
        <tr
          onClick={() => toggleRow(rowKey, isDwa, row.name)}
          style={{
            cursor: canExpand ? "pointer" : "default",
            borderBottom: "1px solid var(--border-light)",
            background: indent > 0 ? `rgba(0,0,0,${indent * 0.015})` : undefined,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#f5f5f0")}
          onMouseLeave={(e) => (e.currentTarget.style.background = indent > 0 ? `rgba(0,0,0,${indent * 0.015})` : "")}
        >
          {COLUMNS.map((col, ci) => {
            const isName = col.key === "name";
            return (
              <td
                key={col.key}
                style={{
                  padding: isName ? "7px 10px" : "7px 8px",
                  fontSize: 12,
                  textAlign: col.numeric ? "right" : "left",
                  verticalAlign: "middle",
                  color: "var(--text-primary)",
                  minWidth: col.width,
                  maxWidth: isName ? 400 : undefined,
                  borderRight: ci < COLUMNS.length - 1 ? "1px solid var(--border-light)" : undefined,
                }}
              >
                {isName ? (
                  <div style={{
                    display: "flex", alignItems: "center",
                    gap: 5, paddingLeft: indent * 20,
                  }}>
                    <ChevronIcon open={isExpanded} />
                    <LevelBadge level={row.level} />
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
        {isDwa && isExpanded && (
          <tr style={{ borderBottom: "1px solid var(--border)" }}>
            <td colSpan={COLUMNS.length} style={{ padding: 0, background: "#fafaf8" }}>
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
                          <WATaskSubRow key={t.task_normalized} task={t} geo={geo} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </td>
          </tr>
        )}

        {/* Inline IWA/GWA child rows */}
        {!isDwa && isExpanded && children.map((child, ci) => {
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
            WA Explorer
          </h1>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            {topRows.length.toLocaleString()} {viewLevel.toUpperCase()} rows
          </span>
        </div>

        {/* Row 2: GWA pills */}
        <div style={{
          display: "flex", flexWrap: "wrap", gap: 5,
          maxHeight: 72, overflowY: "auto",
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
                  maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                  title: gwa,
                } as React.CSSProperties}
              >{gwa}</button>
            );
          })}
        </div>

        {/* Row 3: controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600 }}>Level:</span>
            <BtnSeg<WALevel>
              opts={[{ v: "gwa", l: "GWA" }, { v: "iwa", l: "IWA" }, { v: "dwa", l: "DWA" }]}
              val={viewLevel}
              onChange={(v) => {
                setViewLevel(v);
                setExpandedRows(new Set());
              }}
            />
          </div>

          <input
            type="text"
            placeholder="Search activity name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              fontSize: 12, padding: "4px 10px", borderRadius: 5,
              border: "1px solid var(--border)", outline: "none",
              color: "var(--text-primary)", background: "var(--bg-surface)",
              minWidth: 220,
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

          <button
            onClick={handleReset}
            style={{
              fontSize: 11, padding: "4px 12px", borderRadius: 5,
              border: "1px solid var(--border)", background: "transparent",
              color: "var(--text-secondary)", cursor: "pointer",
            }}
          >Reset</button>
        </div>
      </div>

      {/* ── Table ──────────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowX: "auto", overflowY: "auto" }}>
        <table style={{
          borderCollapse: "collapse",
          tableLayout: "fixed",
          minWidth: COLUMNS.reduce((s, c) => s + c.width, 0),
          width: "100%",
        }}>
          <thead style={{
            position: "sticky", top: 0, zIndex: 10,
            background: "var(--bg-surface)",
            boxShadow: "0 1px 0 var(--border)",
          }}>
            <tr>
              {COLUMNS.map((col) => {
                const hasFilter = !!(colFilters[col.key]?.min || colFilters[col.key]?.max);
                return (
                  <th
                    key={col.key}
                    style={{
                      padding: "8px 8px",
                      textAlign: col.numeric ? "right" : "left",
                      fontSize: 10, fontWeight: 700,
                      color: sortCol === col.key ? "var(--brand)" : "var(--text-muted)",
                      textTransform: "uppercase", letterSpacing: "0.06em",
                      width: col.width, minWidth: col.width,
                      whiteSpace: "nowrap", userSelect: "none",
                      cursor: "pointer",
                      position: "relative",
                    }}
                    onClick={() => handleSort(col.key)}
                  >
                    <div style={{
                      display: "inline-flex", alignItems: "center", gap: 3,
                      justifyContent: col.numeric ? "flex-end" : "flex-start",
                      width: "100%",
                    }}>
                      {col.label}
                      {col.tooltip && <InfoTooltip text={col.tooltip} />}
                      <SortIcon col={col.key} sortCol={sortCol} sortDir={sortDir} />
                      {col.numeric && (
                        <span
                          style={{ cursor: "pointer", display: "inline-flex", alignItems: "center" }}
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenFilter((prev) => (prev === col.key ? null : col.key));
                          }}
                        >
                          <FunnelIcon active={hasFilter} />
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
            {topRows.length === 0 && (
              <tr>
                <td colSpan={COLUMNS.length} style={{
                  padding: "40px 20px", textAlign: "center",
                  fontSize: 13, color: "var(--text-muted)",
                }}>
                  No rows match the current filters.
                </td>
              </tr>
            )}
            {topRows.map((row, i) => renderDataRow(row, 0, `${viewLevel}__${row.name}__${i}`))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
