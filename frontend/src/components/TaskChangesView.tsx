"use client";

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { useSimpleMode } from "@/lib/SimpleModeContext";
import { fetchTaskChanges, fetchAllEcoTasks } from "@/lib/api";
import type { ConfigResponse, TaskChangeRow, TaskChangeStatus, EcoTaskRow, McpEntry } from "@/lib/types";

/* ── Utilities ────────────────────────────────────────────────────────────── */

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState<T>(value);
  useEffect(() => { const t = setTimeout(() => setDebounced(value), delay); return () => clearTimeout(t); }, [value, delay]);
  return debounced;
}

function InfoTooltip({ text }: { text: string }) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null);
  const W = 300, H = 60;
  const clamp = (x: number, y: number) => ({
    x: typeof window !== "undefined" ? Math.min(x, window.innerWidth - W - 10) : x,
    y: typeof window !== "undefined" && y + H > window.innerHeight ? y - H - 10 : y,
  });
  return (
    <span style={{ position: "relative", display: "inline-flex", alignItems: "center", marginLeft: 3 }}>
      <span
        onMouseEnter={(e) => setPos(clamp(e.clientX + 12, e.clientY + 14))}
        onMouseMove={(e) => setPos(clamp(e.clientX + 12, e.clientY + 14))}
        onMouseLeave={() => setPos(null)}
        style={{ cursor: "help", color: "var(--text-muted)", fontSize: 9, fontWeight: 700, border: "1px solid var(--border)", borderRadius: "50%", width: 12, height: 12, display: "inline-flex", alignItems: "center", justifyContent: "center", lineHeight: 1, userSelect: "none" }}
      >?</span>
      {pos && typeof document !== "undefined" && createPortal(
        <div style={{ position: "fixed", left: pos.x, top: pos.y, background: "#1a1a1a", color: "#fff", fontSize: 11, padding: "6px 10px", borderRadius: 6, maxWidth: W, zIndex: 9999, pointerEvents: "none", boxShadow: "0 2px 8px rgba(0,0,0,0.25)", lineHeight: 1.45 }}>{text}</div>,
        document.body,
      )}
    </span>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: open ? "rotate(0deg)" : "rotate(-90deg)", transition: "transform 0.18s ease", flexShrink: 0, color: "var(--text-muted)" }} aria-hidden="true">
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

function BtnSeg<T extends string>({ opts, val, onChange }: { opts: { v: T; l: string }[]; val: T; onChange: (v: T) => void }) {
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

/** Title-case a string: capitalize first letter of each sentence. */
function titleCaseTask(s: string): string {
  if (!s) return s;
  // If all lowercase, capitalize first letter
  if (s === s.toLowerCase()) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  return s;
}

/* ── Status config ────────────────────────────────────────────────────────── */

const STATUS_CONFIG: Record<TaskChangeStatus, { label: string; color: string; bg: string }> = {
  new:             { label: "New",             color: "#15803d", bg: "#dcfce7" },
  changed:         { label: "Changed",         color: "#c2410c", bg: "#fff7ed" },
  removed:         { label: "Removed",         color: "#b91c1c", bg: "#fef2f2" },
  unchanged:       { label: "Unchanged",       color: "#6b7280", bg: "#f3f4f6" },
  not_in_baseline: { label: "Not in baseline", color: "#9ca3af", bg: "#f9fafb" },
};

const DEFAULT_VISIBLE_STATUSES = new Set<TaskChangeStatus>(["new", "changed", "removed"]);

/* ── Column defs ──────────────────────────────────────────────────────────── */

interface ColDef {
  key: string;
  label: string;
  width: number;
  numeric: boolean;
  tooltip?: string;
  textFilter?: boolean;
}

const COLUMNS: ColDef[] = [
  { key: "task",       label: "Task",         width: 300, numeric: false },
  { key: "occ",        label: "Occupation",   width: 220, numeric: false, textFilter: true },
  { key: "major",      label: "Major",        width: 180, numeric: false, textFilter: true },
  { key: "minor",      label: "Minor",        width: 180, numeric: false, textFilter: true },
  { key: "broad",      label: "Broad",        width: 200, numeric: false, textFilter: true },
  { key: "gwa",        label: "GWA",          width: 200, numeric: false, textFilter: true },
  { key: "iwa",        label: "IWA",          width: 200, numeric: false, textFilter: true },
  { key: "dwa",        label: "DWA",          width: 200, numeric: false, textFilter: true },
  { key: "status",     label: "Status",       width: 90,  numeric: false },
  { key: "from_aug",   label: "From Auto",    width: 90,  numeric: true },
  { key: "to_aug",     label: "To Auto",      width: 90,  numeric: true },
  { key: "delta_aug",  label: "\u0394 Auto",  width: 80,  numeric: true, tooltip: "To minus From. Green = increase, red = decrease." },
  { key: "physical",   label: "Physical",     width: 70,  numeric: false },
  { key: "freq",       label: "Freq",         width: 70,  numeric: true },
  { key: "imp",        label: "Importance",   width: 90,  numeric: true },
  { key: "rel",        label: "Relevance",    width: 85,  numeric: true },
  { key: "emp",        label: "Employment",   width: 110, numeric: true },
  { key: "wage",       label: "Median Wage",  width: 110, numeric: true },
  { key: "from_pct",   label: "From pct",     width: 90,  numeric: true },
  { key: "to_pct",     label: "To pct",       width: 90,  numeric: true },
  { key: "delta_pct",  label: "\u0394 pct",   width: 80,  numeric: true },
];

const DEFAULT_HIDDEN = new Set(["minor", "broad", "gwa", "iwa", "dwa", "physical", "freq", "imp", "rel", "emp", "wage", "from_pct", "to_pct", "delta_pct"]);
const SIMPLE_COLS = new Set(["task", "occ", "major", "status", "from_aug", "to_aug", "delta_aug"]);
const ACTIVITY_COLS = new Set(["gwa", "iwa", "dwa"]);
const TEXT_FILTER_COLS = new Set(COLUMNS.filter((c) => c.textFilter).map((c) => c.key));

/* ── Value helpers ────────────────────────────────────────────────────────── */

function getColValue(row: TaskChangeRow, key: string, geo: "nat" | "ut"): string | number | boolean | null | undefined {
  switch (key) {
    case "task":      return row.task;
    case "occ":       return row.title_current;
    case "major":     return row.major_occ_category;
    case "minor":     return row.minor_occ_category;
    case "broad":     return row.broad_occ;
    case "gwa":       return row.gwa_title;
    case "iwa":       return row.iwa_title;
    case "dwa":       return row.dwa_title;
    case "status":    return row.status;
    case "from_aug":  return row.from_auto_aug;
    case "to_aug":    return row.to_auto_aug;
    case "delta_aug": return row.delta_auto_aug;
    case "physical":  return row.physical;
    case "freq":      return row.freq_mean;
    case "imp":       return row.importance;
    case "rel":       return row.relevance;
    case "emp":       return geo === "nat" ? row.emp_nat : row.emp_ut;
    case "wage":      return geo === "nat" ? row.wage_nat : row.wage_ut;
    case "from_pct":  return row.from_pct;
    case "to_pct":    return row.to_pct;
    case "delta_pct": return row.delta_pct;
    default:          return null;
  }
}

function getNumericValue(row: TaskChangeRow, key: string, geo: "nat" | "ut"): number | null {
  const v = getColValue(row, key, geo);
  if (v == null || typeof v === "string" || typeof v === "boolean") return null;
  return v;
}

function fmtNum(v: number | null | undefined, decimals = 2): string {
  if (v == null) return "\u2014";
  return v.toFixed(decimals);
}

function fmtEmp(v: number | null | undefined): string {
  if (v == null) return "\u2014";
  return Math.round(v).toLocaleString();
}

function fmtWage(v: number | null | undefined): string {
  if (v == null) return "\u2014";
  return "$" + Math.round(v).toLocaleString();
}

function fmtCell(key: string, val: string | number | boolean | null | undefined): string {
  if (val == null) return "\u2014";
  if (key === "physical") return val ? "\u2713" : "";
  if (key === "emp") return fmtEmp(val as number);
  if (key === "wage") return fmtWage(val as number);
  if (key === "from_aug" || key === "to_aug" || key === "delta_aug") return fmtNum(val as number, 2);
  if (key === "from_pct" || key === "to_pct" || key === "delta_pct") return fmtNum(val as number, 4);
  if (key === "freq" || key === "imp" || key === "rel") return fmtNum(val as number, 2);
  if (key === "status") return STATUS_CONFIG[val as TaskChangeStatus]?.label ?? String(val);
  return String(val);
}

function highlightText(text: string, query: string): React.ReactNode {
  if (!query) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx < 0) return text;
  return <>{text.slice(0, idx)}<mark style={{ background: "#fde68a", borderRadius: 2 }}>{text.slice(idx, idx + query.length)}</mark>{text.slice(idx + query.length)}</>;
}

/* ── Numeric filter dropdown ──────────────────────────────────────────────── */

function NumericFilterDropdown({
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
    setFilters((prev) => {
      const prevCur = prev[colKey] ?? { min: "", max: "" };
      return { ...prev, [colKey]: { ...prevCur, [field]: val } };
    });
  };

  const hasFilter = cur.min !== "" || cur.max !== "";

  return (
    <div ref={ref} onClick={(e) => e.stopPropagation()} onMouseDown={(e) => e.stopPropagation()} style={{
      position: "absolute", top: "100%", right: 0, zIndex: 500,
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 7, padding: "10px 12px", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      minWidth: 140, display: "flex", flexDirection: "column", gap: 7,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 10, color: "var(--text-muted)", width: 14 }}>&ge;</span>
        <input type="number" value={cur.min} onChange={(e) => setMinMax("min", e.target.value)} placeholder="min"
          style={{ width: "100%", fontSize: 11, padding: "4px 6px", border: "1px solid var(--border)", borderRadius: 4, outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)" }} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ fontSize: 10, color: "var(--text-muted)", width: 14 }}>&le;</span>
        <input type="number" value={cur.max} onChange={(e) => setMinMax("max", e.target.value)} placeholder="max"
          style={{ width: "100%", fontSize: 11, padding: "4px 6px", border: "1px solid var(--border)", borderRadius: 4, outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)" }} />
      </div>
      {hasFilter && (
        <button onClick={() => setFilters((prev) => ({ ...prev, [colKey]: { min: "", max: "" } }))}
          style={{ fontSize: 10, color: "var(--brand)", background: "none", border: "none", cursor: "pointer", padding: 0, textAlign: "left" }}>
          Clear
        </button>
      )}
    </div>
  );
}

/* ── Text filter dropdown ─────────────────────────────────────────────────── */

function TextFilterDropdown({
  colKey,
  uniqueValues,
  selectedValues,
  onSelectionChange,
  onClose,
}: {
  colKey: string;
  uniqueValues: string[];
  selectedValues: Set<string> | null;
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
    <div ref={ref} onClick={(e) => e.stopPropagation()} onMouseDown={(e) => e.stopPropagation()} style={{
      position: "absolute", top: "100%", left: 0, zIndex: 500,
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 7, padding: "8px 0", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      minWidth: 220, maxWidth: 320, display: "flex", flexDirection: "column",
    }}>
      <div style={{ padding: "0 8px 6px" }}>
        <input type="text" placeholder="Search..." value={filterSearch} onChange={(e) => setFilterSearch(e.target.value)}
          style={{ width: "100%", fontSize: 11, padding: "4px 6px", border: "1px solid var(--border)", borderRadius: 4, outline: "none", color: "var(--text-primary)", background: "var(--bg-surface)", boxSizing: "border-box" }} />
      </div>
      <label style={{ display: "flex", alignItems: "center", gap: 8, padding: "3px 10px", fontSize: 11, cursor: "pointer", color: "var(--text-primary)", fontWeight: 600, borderBottom: "1px solid var(--border-light)" }}>
        <input type="checkbox" checked={isAll} onChange={() => { onSelectionChange(colKey, isAll ? new Set() : null); }} style={{ margin: 0 }} />
        All ({uniqueValues.length})
      </label>
      <div style={{ maxHeight: 250, overflowY: "auto" }}>
        {filtered.map((val) => {
          const checked = isAll || (selectedValues?.has(val) ?? false);
          return (
            <label key={val} style={{ display: "flex", alignItems: "center", gap: 8, padding: "3px 10px", fontSize: 11, cursor: "pointer", color: checked ? "var(--text-primary)" : "var(--text-muted)" }}>
              <input type="checkbox" checked={checked} onChange={() => {
                if (isAll) {
                  const all = new Set(uniqueValues);
                  all.delete(val);
                  onSelectionChange(colKey, all);
                } else {
                  const next = new Set(selectedValues);
                  if (next.has(val)) next.delete(val); else next.add(val);
                  if (next.size === uniqueValues.length) onSelectionChange(colKey, null);
                  else onSelectionChange(colKey, next);
                }
              }} style={{ margin: 0 }} />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{val}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

/* ── Component ────────────────────────────────────────────────────────────── */

interface Props {
  config: ConfigResponse;
}

export default function TaskChangesView({ config }: Props) {
  const { isSimple } = useSimpleMode();
  const datasets = config.datasets;

  // ── Dataset pickers ──
  const [fromDataset, setFromDataset] = useState("AEI Cumul. v1");
  const [toDataset, setToDataset] = useState("AEI Cumul. v4");

  // ── Data state ──
  const [rows, setRows] = useState<TaskChangeRow[] | null>(null);
  const [ecoTasks, setEcoTasks] = useState<EcoTaskRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRun, setHasRun] = useState(false);

  // ── Filters ──
  const [visibleStatuses, setVisibleStatuses] = useState<Set<TaskChangeStatus>>(new Set(DEFAULT_VISIBLE_STATUSES));
  const [selectedMajors, setSelectedMajors] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 250);
  const [physicalMode, setPhysicalMode] = useState<"all" | "exclude" | "only">("all");
  const [geo, setGeo] = useState<"nat" | "ut">("nat");
  const [colFilters, setColFilters] = useState<Record<string, { min: string; max: string }>>({});
  const [openFilter, setOpenFilter] = useState<string | null>(null);
  const [textColFilters, setTextColFilters] = useState<Record<string, Set<string> | null>>({});
  const [openTextFilter, setOpenTextFilter] = useState<string | null>(null);

  // ── Column visibility ──
  const [hiddenCols, setHiddenCols] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set(DEFAULT_HIDDEN);
    try {
      const saved = localStorage.getItem("aea_tc_hidden_cols");
      return saved ? new Set(JSON.parse(saved) as string[]) : new Set(DEFAULT_HIDDEN);
    } catch { return new Set(DEFAULT_HIDDEN); }
  });
  const [colSelectorOpen, setColSelectorOpen] = useState(false);
  const colSelectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try { localStorage.setItem("aea_tc_hidden_cols", JSON.stringify(Array.from(hiddenCols))); } catch { /* silent */ }
  }, [hiddenCols]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (colSelectorRef.current && !colSelectorRef.current.contains(e.target as Node)) setColSelectorOpen(false);
    };
    if (colSelectorOpen) { document.addEventListener("mousedown", handler); return () => document.removeEventListener("mousedown", handler); }
  }, [colSelectorOpen]);

  // ── Sort ──
  const [sortCol, setSortCol] = useState("status");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const handleSort = (col: string) => {
    if (sortCol === col) setSortDir((d) => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("desc"); }
  };

  // ── Pagination ──
  const [rowLimit, setRowLimit] = useState(100);
  useEffect(() => { setRowLimit(100); }, [debouncedSearch, selectedMajors, visibleStatuses, physicalMode, sortCol, sortDir, colFilters, textColFilters]);

  // ── Expansion ──
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // ── Auto-run in simple mode ──
  const autoRunRef = useRef(false);
  useEffect(() => {
    if (isSimple && !autoRunRef.current) {
      autoRunRef.current = true;
      runComparison();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSimple]);

  // ── Run comparison ──
  const runComparison = useCallback(async () => {
    setLoading(true);
    setError(null);
    setExpandedRows(new Set());
    try {
      const [result, eco] = await Promise.all([
        fetchTaskChanges(fromDataset, toDataset),
        ecoTasks ? Promise.resolve({ tasks: ecoTasks }) : fetchAllEcoTasks(),
      ]);
      setRows(result.rows);
      if (!ecoTasks) setEcoTasks(eco.tasks);
      setHasRun(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [fromDataset, toDataset, ecoTasks]);

  // ── Eco task activity index for row expansion ──
  const ecoActivityIndex = useMemo(() => {
    if (!ecoTasks) return new Map<string, EcoTaskRow[]>();
    const idx = new Map<string, EcoTaskRow[]>();
    for (const t of ecoTasks) {
      const k = `${t.task_normalized}\0${t.title_current}`;
      const arr = idx.get(k);
      if (arr) arr.push(t); else idx.set(k, [t]);
    }
    return idx;
  }, [ecoTasks]);

  // ── Determine if activity columns are visible ──
  const showActivities = useMemo(() => {
    return Array.from(ACTIVITY_COLS).some((c) => !hiddenCols.has(c));
  }, [hiddenCols]);

  // ── Expand rows when activity columns visible ──
  const expandedData = useMemo((): TaskChangeRow[] => {
    if (!rows) return [];
    if (!showActivities || !ecoTasks) return rows;

    const result: TaskChangeRow[] = [];
    for (const row of rows) {
      const k = `${row.task_normalized}\0${row.title_current}`;
      const activityRows = ecoActivityIndex.get(k);
      if (!activityRows || activityRows.length <= 1) {
        result.push(row);
        continue;
      }
      const seen = new Set<string>();
      for (const eco of activityRows) {
        const dedup = `${eco.dwa_title}\0${eco.iwa_title}\0${eco.gwa_title}`;
        if (seen.has(dedup)) continue;
        seen.add(dedup);
        result.push({
          ...row,
          dwa_title: eco.dwa_title,
          iwa_title: eco.iwa_title,
          gwa_title: eco.gwa_title,
        });
      }
    }
    return result;
  }, [rows, showActivities, ecoTasks, ecoActivityIndex]);

  // ── Major list ──
  const allMajors = useMemo(() => {
    if (!rows) return [];
    const s = new Set(rows.map((r) => r.major_occ_category ?? "Unknown"));
    return Array.from(s).sort();
  }, [rows]);

  // ── Visible columns ──
  const visibleCols = useMemo(() => {
    return COLUMNS.filter((c) => {
      if (c.key === "task") return true;
      if (isSimple && !SIMPLE_COLS.has(c.key)) return false;
      if (hiddenCols.has(c.key)) return false;
      return true;
    });
  }, [hiddenCols, isSimple]);

  // ── Text column unique values (for text filter dropdowns) ──
  const textColUniqueValues = useMemo(() => {
    const getters: Record<string, (r: TaskChangeRow) => string | null | undefined> = {
      occ: (r) => r.title_current,
      major: (r) => r.major_occ_category,
      minor: (r) => r.minor_occ_category,
      broad: (r) => r.broad_occ,
      gwa: (r) => r.gwa_title,
      iwa: (r) => r.iwa_title,
      dwa: (r) => r.dwa_title,
    };
    const result: Record<string, string[]> = {};
    for (const [key, getter] of Object.entries(getters)) {
      const vals = new Set<string>();
      for (const r of expandedData) {
        const v = getter(r);
        if (v) vals.add(v);
      }
      result[key] = Array.from(vals).sort();
    }
    return result;
  }, [expandedData]);

  // ── Filter + sort ──
  const processedRows = useMemo(() => {
    let data = expandedData;

    // Status filter
    data = data.filter((r) => visibleStatuses.has(r.status));

    // Major filter
    if (selectedMajors.size > 0) {
      data = data.filter((r) => selectedMajors.has(r.major_occ_category ?? "Unknown"));
    }

    // Physical filter
    if (physicalMode === "exclude") data = data.filter((r) => r.physical !== true);
    else if (physicalMode === "only") data = data.filter((r) => r.physical === true);

    // Search
    if (debouncedSearch) {
      const q = debouncedSearch.toLowerCase();
      data = data.filter((r) => {
        const fields = [r.task, r.title_current, r.major_occ_category, r.minor_occ_category, r.broad_occ, r.gwa_title, r.iwa_title, r.dwa_title];
        return fields.some((f) => f?.toLowerCase().includes(q));
      });
    }

    // Numeric column filters
    Object.entries(colFilters).forEach(([key, { min, max }]) => {
      const minN = min !== "" ? parseFloat(min) : null;
      const maxN = max !== "" ? parseFloat(max) : null;
      if (minN !== null || maxN !== null) {
        data = data.filter((r) => {
          const v = getNumericValue(r, key, geo);
          if (minN !== null && (v == null || v < minN)) return false;
          if (maxN !== null && (v == null || v > maxN)) return false;
          return true;
        });
      }
    });

    // Text column filters
    const textGetters: Record<string, (r: TaskChangeRow) => string | null | undefined> = {
      occ: (r) => r.title_current,
      major: (r) => r.major_occ_category,
      minor: (r) => r.minor_occ_category,
      broad: (r) => r.broad_occ,
      gwa: (r) => r.gwa_title,
      iwa: (r) => r.iwa_title,
      dwa: (r) => r.dwa_title,
    };
    for (const [colKey, selected] of Object.entries(textColFilters)) {
      if (selected === null || selected === undefined) continue;
      if (selected.size === 0) { data = []; break; }
      const getter = textGetters[colKey];
      if (getter) {
        data = data.filter((r) => {
          const v = getter(r);
          return v != null && selected.has(v);
        });
      }
    }

    // Sort
    const statusOrder: Record<TaskChangeStatus, number> = { new: 0, changed: 1, removed: 2, unchanged: 3, not_in_baseline: 4 };
    data = [...data].sort((a, b) => {
      let av: number | string | null = null;
      let bv: number | string | null = null;
      if (sortCol === "status") {
        av = statusOrder[a.status] ?? 99;
        bv = statusOrder[b.status] ?? 99;
      } else {
        const aVal = getColValue(a, sortCol, geo);
        const bVal = getColValue(b, sortCol, geo);
        av = aVal == null ? null : typeof aVal === "string" ? aVal.toLowerCase() : Number(aVal);
        bv = bVal == null ? null : typeof bVal === "string" ? bVal.toLowerCase() : Number(bVal);
      }
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });

    return data;
  }, [expandedData, visibleStatuses, selectedMajors, physicalMode, debouncedSearch, sortCol, sortDir, geo, colFilters, textColFilters]);

  // ── Status summary counts — computed from processedRows (post-filter) ──
  const statusCounts = useMemo(() => {
    // Count from rows that pass major/search/physical/column filters but ignore status filter
    let data = expandedData;
    if (selectedMajors.size > 0) {
      data = data.filter((r) => selectedMajors.has(r.major_occ_category ?? "Unknown"));
    }
    if (physicalMode === "exclude") data = data.filter((r) => r.physical !== true);
    else if (physicalMode === "only") data = data.filter((r) => r.physical === true);
    if (debouncedSearch) {
      const q = debouncedSearch.toLowerCase();
      data = data.filter((r) => {
        const fields = [r.task, r.title_current, r.major_occ_category, r.minor_occ_category, r.broad_occ, r.gwa_title, r.iwa_title, r.dwa_title];
        return fields.some((f) => f?.toLowerCase().includes(q));
      });
    }
    // Apply numeric column filters
    Object.entries(colFilters).forEach(([key, { min, max }]) => {
      const minN = min !== "" ? parseFloat(min) : null;
      const maxN = max !== "" ? parseFloat(max) : null;
      if (minN !== null || maxN !== null) {
        data = data.filter((r) => {
          const v = getNumericValue(r, key, geo);
          if (minN !== null && (v == null || v < minN)) return false;
          if (maxN !== null && (v == null || v > maxN)) return false;
          return true;
        });
      }
    });
    // Apply text column filters
    const textGetters: Record<string, (r: TaskChangeRow) => string | null | undefined> = {
      occ: (r) => r.title_current, major: (r) => r.major_occ_category,
      minor: (r) => r.minor_occ_category, broad: (r) => r.broad_occ,
      gwa: (r) => r.gwa_title, iwa: (r) => r.iwa_title, dwa: (r) => r.dwa_title,
    };
    for (const [colKey, selected] of Object.entries(textColFilters)) {
      if (selected === null || selected === undefined) continue;
      if (selected.size === 0) { data = []; break; }
      const getter = textGetters[colKey];
      if (getter) data = data.filter((r) => { const v = getter(r); return v != null && selected.has(v); });
    }
    const counts: Record<string, number> = {};
    for (const r of data) counts[r.status] = (counts[r.status] ?? 0) + 1;
    return counts as Record<TaskChangeStatus, number>;
  }, [expandedData, selectedMajors, physicalMode, debouncedSearch, colFilters, textColFilters, geo]);

  const shownRows = processedRows.slice(0, rowLimit);

  // ── Toggle row expansion ──
  const toggleRow = useCallback((key: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }, []);

  /* ═══════════════════════════════════════════════════════════════════════════ */
  /* RENDER                                                                     */
  /* ═══════════════════════════════════════════════════════════════════════════ */

  return (
    <div style={{ padding: "20px 24px 40px", maxWidth: 1800, margin: "0 auto" }}>
      {/* ── Title ── */}
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4, color: "var(--text-primary)" }}>Task Changes Explorer</h1>
      <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16 }}>
        Compare two dataset versions at the task level to see which tasks were added, removed, or changed.
      </p>

      {/* ── Dataset pickers + Run ── */}
      {!isSimple ? (
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)" }}>From:</label>
            <select value={fromDataset} onChange={(e) => setFromDataset(e.target.value)}
              style={{ fontSize: 12, padding: "4px 8px", border: "1px solid var(--border)", borderRadius: 5, background: "var(--bg-surface)", color: "var(--text-primary)" }}>
              {datasets.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <span style={{ fontSize: 14, color: "var(--text-muted)" }}>&rarr;</span>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)" }}>To:</label>
            <select value={toDataset} onChange={(e) => setToDataset(e.target.value)}
              style={{ fontSize: 12, padding: "4px 8px", border: "1px solid var(--border)", borderRadius: 5, background: "var(--bg-surface)", color: "var(--text-primary)" }}>
              {datasets.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <button onClick={runComparison} disabled={loading}
            style={{ padding: "5px 16px", fontSize: 12, fontWeight: 600, borderRadius: 6, border: "none", background: "var(--brand)", color: "#fff", cursor: loading ? "wait" : "pointer", opacity: loading ? 0.7 : 1 }}>
            {loading ? "Running..." : "Run"}
          </button>
        </div>
      ) : (
        <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 16, padding: "6px 12px", background: "var(--brand-light)", borderRadius: 6, display: "inline-block" }}>
          Comparing <strong>AEI Cumul. v1</strong> &rarr; <strong>AEI Cumul. v4</strong>
        </div>
      )}

      {error && <p style={{ color: "#b91c1c", fontSize: 12, marginBottom: 12 }}>Error: {error}</p>}

      {!hasRun && !loading && (
        <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-muted)", fontSize: 13 }}>
          Select two datasets and click Run to compare.
        </div>
      )}

      {loading && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 0", gap: 12 }}>
          <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>Computing task changes...</p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {hasRun && !loading && rows && (
        <>
          {/* ── Status summary (dynamic counts) ── */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
            {(Object.entries(STATUS_CONFIG) as [TaskChangeStatus, typeof STATUS_CONFIG[TaskChangeStatus]][]).map(([status, cfg]) => {
              const count = statusCounts[status] ?? 0;
              const active = visibleStatuses.has(status);
              return (
                <button key={status} onClick={() => {
                  setVisibleStatuses((prev) => {
                    const next = new Set(prev);
                    if (next.has(status)) next.delete(status); else next.add(status);
                    return next;
                  });
                }}
                  style={{
                    fontSize: 11, padding: "4px 10px", borderRadius: 12,
                    border: `1.5px solid ${active ? cfg.color : "var(--border)"}`,
                    background: active ? cfg.bg : "transparent",
                    color: active ? cfg.color : "var(--text-muted)",
                    cursor: "pointer", fontWeight: active ? 600 : 400,
                    opacity: active ? 1 : 0.6,
                    fontStyle: status === "not_in_baseline" ? "italic" : "normal",
                  }}>
                  {cfg.label}: {count}
                </button>
              );
            })}
          </div>

          {/* ── Controls bar ── */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
            {/* Search */}
            <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
              <span style={{ position: "absolute", left: 8, color: "var(--text-muted)", pointerEvents: "none" }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </span>
              <input type="text" placeholder="Search tasks, occupations..." value={search} onChange={(e) => setSearch(e.target.value)}
                style={{ paddingLeft: 28, paddingRight: 24, paddingTop: 5, paddingBottom: 5, fontSize: 12, border: "1px solid var(--border)", borderRadius: 6, outline: "none", background: "var(--bg-surface)", color: "var(--text-primary)", width: 240 }} />
              {search && <button onClick={() => setSearch("")} style={{ position: "absolute", right: 6, background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: 14, lineHeight: 1, padding: 0 }}>&times;</button>}
            </div>

            {/* Geo toggle */}
            <BtnSeg opts={[{ v: "nat" as const, l: "Nat" }, { v: "ut" as const, l: "Utah" }]} val={geo} onChange={setGeo} />

            {/* Physical filter (advanced only) */}
            {!isSimple && (
              <BtnSeg
                opts={[{ v: "all" as const, l: "All" }, { v: "exclude" as const, l: "No Phys" }, { v: "only" as const, l: "Phys only" }]}
                val={physicalMode} onChange={setPhysicalMode}
              />
            )}

            {/* Spacer + column selector */}
            <div style={{ marginLeft: "auto", position: "relative" }} ref={colSelectorRef}>
              <button onClick={() => setColSelectorOpen((o) => !o)}
                style={{ background: "none", border: "1px solid var(--border)", borderRadius: 5, padding: "4px 8px", cursor: "pointer", fontSize: 11, color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: 4 }}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" /></svg>
                Columns
              </button>
              {colSelectorOpen && (
                <div style={{ position: "absolute", right: 0, top: "100%", marginTop: 4, background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 0", zIndex: 100, boxShadow: "0 4px 16px rgba(0,0,0,0.12)", width: 200, maxHeight: 400, overflowY: "auto" }}>
                  {COLUMNS.filter((c) => c.key !== "task").map((c) => {
                    if (isSimple && !SIMPLE_COLS.has(c.key)) return null;
                    const checked = !hiddenCols.has(c.key);
                    return (
                      <label key={c.key} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 12px", fontSize: 11, cursor: "pointer", color: checked ? "var(--text-primary)" : "var(--text-muted)" }}
                        onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#f5f5f3"; }}
                        onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
                        <input type="checkbox" checked={checked} onChange={() => {
                          setHiddenCols((prev) => { const next = new Set(prev); if (next.has(c.key)) next.delete(c.key); else next.add(c.key); return next; });
                        }} style={{ margin: 0 }} />
                        {c.label}
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* ── Major pills ── */}
          {allMajors.length > 0 && (
            <div style={{ display: "flex", gap: 5, flexWrap: "wrap", marginBottom: 10, maxHeight: 64, overflowY: "auto" }}>
              {allMajors.map((maj) => {
                const sel = selectedMajors.has(maj);
                return (
                  <button key={maj} onClick={() => {
                    setSelectedMajors((prev) => { const next = new Set(prev); if (next.has(maj)) next.delete(maj); else next.add(maj); return next; });
                  }}
                    style={{ flexShrink: 0, fontSize: 10, padding: "2px 8px", borderRadius: 10, border: `1.5px solid ${sel ? "var(--brand)" : "var(--border)"}`, background: sel ? "var(--brand-light)" : "transparent", color: sel ? "var(--brand)" : "var(--text-secondary)", cursor: "pointer", fontWeight: sel ? 600 : 400, whiteSpace: "nowrap" }}>
                    {maj}
                  </button>
                );
              })}
            </div>
          )}

          {/* ── Table ── */}
          <div style={{ border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
            <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "calc(100vh - 320px)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, tableLayout: "fixed", minWidth: visibleCols.reduce((s, c) => s + c.width, 0) }}>
                <colgroup>
                  {visibleCols.map((c) => <col key={c.key} style={{ width: c.width }} />)}
                </colgroup>
                <thead>
                  <tr style={{ background: "var(--bg-surface)", borderBottom: "2px solid var(--border)", position: "sticky", top: 0, zIndex: 10 }}>
                    {visibleCols.map((col) => {
                      const hasNumFilter = col.numeric && !!(colFilters[col.key]?.min || colFilters[col.key]?.max);
                      const isTextFilterCol = TEXT_FILTER_COLS.has(col.key);
                      const hasTextFilter = isTextFilterCol && textColFilters[col.key] !== null && textColFilters[col.key] !== undefined;
                      return (
                        <th key={col.key} onClick={() => handleSort(col.key)}
                          style={{ padding: "7px 8px", textAlign: col.numeric ? "right" : "left", fontSize: 11, fontWeight: 700, color: sortCol === col.key ? "var(--brand)" : "var(--text-muted)", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap", position: "relative" }}>
                          <div style={{ display: "inline-flex", alignItems: "center", gap: 3, paddingRight: (col.numeric || isTextFilterCol) ? 14 : 0 }}>
                            {col.label}
                            {col.tooltip && <InfoTooltip text={col.tooltip} />}
                            {sortCol === col.key && <span style={{ color: "var(--brand)", fontSize: 10 }}>{sortDir === "desc" ? "\u2193" : "\u2191"}</span>}
                          </div>
                          {col.numeric && (
                            <span
                              onClick={(e) => { e.stopPropagation(); setOpenFilter((prev) => prev === col.key ? null : col.key); setOpenTextFilter(null); }}
                              style={{ position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: hasNumFilter ? "var(--brand)" : "var(--text-muted)", opacity: hasNumFilter ? 1 : 0.5, display: "inline-flex" }}
                              title="Filter">
                              <FunnelIcon />
                            </span>
                          )}
                          {openFilter === col.key && (
                            <NumericFilterDropdown colKey={col.key} filters={colFilters} setFilters={setColFilters} onClose={() => setOpenFilter(null)} />
                          )}
                          {isTextFilterCol && (
                            <>
                              <span
                                onClick={(e) => { e.stopPropagation(); setOpenTextFilter((prev) => prev === col.key ? null : col.key); setOpenFilter(null); }}
                                style={{ position: "absolute", right: 4, top: "50%", transform: "translateY(-50%)", cursor: "pointer", color: hasTextFilter ? "var(--brand)" : "var(--text-muted)", opacity: hasTextFilter ? 1 : 0.5, display: "inline-flex" }}
                                title="Filter values">
                                <FunnelIcon />
                              </span>
                              {openTextFilter === col.key && (
                                <TextFilterDropdown
                                  colKey={col.key}
                                  uniqueValues={textColUniqueValues[col.key] ?? []}
                                  selectedValues={textColFilters[col.key] ?? null}
                                  onSelectionChange={(ck, vals) => setTextColFilters((prev) => ({ ...prev, [ck]: vals }))}
                                  onClose={() => setOpenTextFilter(null)}
                                />
                              )}
                            </>
                          )}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {shownRows.map((row, idx) => {
                    const rowKey = `${row.task_normalized}\0${row.title_current}\0${row.dwa_title ?? ""}`;
                    const isExpanded = expandedRows.has(rowKey);
                    const sCfg = STATUS_CONFIG[row.status];
                    return (
                      <React.Fragment key={idx}>
                        <tr onClick={() => toggleRow(rowKey)}
                          style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)" }}
                          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "#f9f9f7"; }}
                          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}>
                          {visibleCols.map((col) => {
                            const rawVal = getColValue(row, col.key, geo);
                            const val = col.key === "task" && typeof rawVal === "string" ? titleCaseTask(rawVal) : rawVal;
                            const isDelta = col.key === "delta_aug" || col.key === "delta_pct";
                            let cellColor = "var(--text-primary)";
                            if (isDelta && typeof val === "number") {
                              cellColor = val > 0 ? "#15803d" : val < 0 ? "#b91c1c" : "var(--text-muted)";
                            }
                            if (col.key === "status") {
                              return (
                                <td key={col.key} style={{ padding: "6px 8px" }}>
                                  <span style={{
                                    display: "inline-block", fontSize: 10, padding: "2px 8px", borderRadius: 10,
                                    background: sCfg.bg, color: sCfg.color, fontWeight: 600,
                                    fontStyle: row.status === "not_in_baseline" ? "italic" : "normal",
                                  }}>
                                    {sCfg.label}
                                  </span>
                                </td>
                              );
                            }
                            if (col.key === "task") {
                              return (
                                <td key={col.key} style={{ padding: "6px 8px", color: "var(--text-primary)", wordBreak: "break-word", whiteSpace: "normal", lineHeight: 1.35 }} title={String(val ?? "")}>
                                  <ChevronIcon open={isExpanded} />
                                  {" "}{highlightText(String(val ?? ""), debouncedSearch)}
                                </td>
                              );
                            }
                            if (col.key === "occ") {
                              return (
                                <td key={col.key} style={{ padding: "6px 8px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: "var(--text-primary)" }} title={String(val ?? "")}>
                                  {highlightText(String(val ?? ""), debouncedSearch)}
                                </td>
                              );
                            }
                            const isText = !col.numeric;
                            return (
                              <td key={col.key} style={{ padding: "6px 8px", textAlign: col.numeric ? "right" : "left", color: isDelta ? cellColor : isText ? "var(--text-secondary)" : "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", fontStyle: row.status === "not_in_baseline" && !isDelta ? "italic" : "normal" }} title={isText ? String(val ?? "") : undefined}>
                                {isText ? highlightText(String(val ?? "\u2014"), debouncedSearch) : fmtCell(col.key, val)}
                              </td>
                            );
                          })}
                        </tr>
                        {isExpanded && (
                          <tr style={{ background: "#f7f7f5", borderBottom: "1px solid var(--border)" }}>
                            <td colSpan={visibleCols.length} style={{ padding: "10px 20px 14px 28px" }}>
                              <ExpandedDetail row={row} />
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                  {shownRows.length === 0 && (
                    <tr><td colSpan={visibleCols.length} style={{ textAlign: "center", padding: "24px 0", color: "var(--text-muted)", fontSize: 12 }}>No rows match the current filters.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            {processedRows.length > rowLimit && (
              <div style={{ padding: "12px 20px", textAlign: "center", borderTop: "1px solid var(--border-light)" }}>
                <span style={{ fontSize: 12, color: "var(--text-muted)", marginRight: 12 }}>
                  Showing {Math.min(rowLimit, processedRows.length).toLocaleString()} of {processedRows.length.toLocaleString()} rows.
                </span>
                <button onClick={() => setRowLimit((r) => r + 100)}
                  style={{ fontSize: 12, color: "var(--brand)", background: "none", border: "none", cursor: "pointer", padding: 0, fontWeight: 600 }}>
                  Load 100 more &rarr;
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ── Expanded detail panel ────────────────────────────────────────────────── */

function fmtPctNorm(v: number | null | undefined): string {
  if (v == null) return "\u2014";
  return v.toFixed(4) + "%";
}

function ExpandedDetail({ row }: { row: TaskChangeRow }) {
  const sectionHead: React.CSSProperties = { fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 5 };
  const detailLabel: React.CSSProperties = { fontSize: 11, color: "var(--text-muted)", minWidth: 90 };
  const detailValue: React.CSSProperties = { fontSize: 11, color: "var(--text-secondary)" };

  return (
    <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
      {/* Occupation Categories */}
      <div style={{ minWidth: 200 }}>
        <p style={sectionHead}>Occupation Categories</p>
        {[
          ["Occupation", row.title_current],
          ["Broad", row.broad_occ],
          ["Minor", row.minor_occ_category],
          ["Major", row.major_occ_category],
        ].map(([label, val]) => (
          <div key={label as string} style={{ display: "flex", gap: 8, marginBottom: 2 }}>
            <span style={detailLabel}>{label}</span>
            <span style={detailValue}>{val ?? "\u2014"}</span>
          </div>
        ))}
      </div>

      {/* Work Activities */}
      <div style={{ minWidth: 200 }}>
        <p style={sectionHead}>Work Activities</p>
        {[
          ["GWA", row.gwa_title],
          ["IWA", row.iwa_title],
          ["DWA", row.dwa_title],
        ].map(([label, val]) => (
          <div key={label as string} style={{ display: "flex", gap: 8, marginBottom: 2 }}>
            <span style={detailLabel}>{label}</span>
            <span style={detailValue}>{val ?? "\u2014"}</span>
          </div>
        ))}
      </div>

      {/* Source Breakdown — styled to match explorers (colored AVG/MAX badges) */}
      {row.sources && Object.keys(row.sources).length > 0 && (
        <div style={{ minWidth: 220 }}>
          <p style={sectionHead}>Source Breakdown</p>
          <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "left" }}>Source</th>
                <th style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Auto Aug</th>
                <th style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Pct Norm</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(row.sources).map(([src, stats]) => (
                <tr key={src}>
                  <td style={{ padding: "2px 10px 2px 0", color: "var(--text-secondary)" }}>{src}</td>
                  <td style={{ padding: "2px 10px 2px 0", color: "var(--text-secondary)", textAlign: "right" }}>{stats.auto_aug?.toFixed(2) ?? "\u2014"}</td>
                  <td style={{ padding: "2px 10px 2px 0", color: "var(--text-secondary)", textAlign: "right" }}>{stats.pct_norm != null ? fmtPctNorm(stats.pct_norm) : "\u2014"}</td>
                </tr>
              ))}
              {/* AVG / MAX footer with colored badges matching explorer style */}
              {(() => {
                const autos = Object.values(row.sources).map((s) => s.auto_aug).filter((v): v is number => v != null);
                const pcts = Object.values(row.sources).map((s) => s.pct_norm).filter((v): v is number => v != null);
                if (autos.length === 0 && pcts.length === 0) return null;
                const avgAuto = autos.length > 0 ? autos.reduce((a, b) => a + b, 0) / autos.length : null;
                const maxAuto = autos.length > 0 ? Math.max(...autos) : null;
                const avgPct = pcts.length > 0 ? pcts.reduce((a, b) => a + b, 0) / pcts.length : null;
                const maxPct = pcts.length > 0 ? Math.max(...pcts) : null;
                return (
                  <>
                    <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                      <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                        <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "var(--brand-light)", border: "1px solid var(--brand)", color: "var(--brand)", fontWeight: 700 }}>AVG</span>
                      </td>
                      <td style={{ padding: "4px 10px 2px 0", textAlign: "right", fontWeight: 700 }}>{avgAuto != null ? avgAuto.toFixed(3) : "\u2014"}</td>
                      <td style={{ padding: "4px 10px 2px 0", textAlign: "right", fontWeight: 700 }}>{avgPct != null ? fmtPctNorm(avgPct) : "\u2014"}</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 4px 0", fontWeight: 700 }}>
                        <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "#fffbeb", border: "1px solid #d97706", color: "#d97706", fontWeight: 700 }}>MAX</span>
                      </td>
                      <td style={{ padding: "2px 10px 4px 0", textAlign: "right", fontWeight: 700 }}>{maxAuto != null ? maxAuto.toFixed(3) : "\u2014"}</td>
                      <td style={{ padding: "2px 10px 4px 0", textAlign: "right", fontWeight: 700 }}>{maxPct != null ? fmtPctNorm(maxPct) : "\u2014"}</td>
                    </tr>
                  </>
                );
              })()}
            </tbody>
          </table>
        </div>
      )}

      {/* Top MCP Servers */}
      {row.top_mcps && row.top_mcps.length > 0 && (
        <div style={{ minWidth: 200 }}>
          <p style={sectionHead}>Top MCP Servers</p>
          <ul style={{ margin: 0, paddingLeft: 16, listStyleType: "disc" }}>
            {row.top_mcps.slice(0, 5).map((mcp: McpEntry, mi: number) => (
              <li key={mi} style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 3 }}>
                {mcp.url
                  ? <a href={mcp.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--brand)", textDecoration: "none" }}>{mcp.title}</a>
                  : mcp.title}
                {mcp.rating != null && <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: 6 }}>({mcp.rating}/5)</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
