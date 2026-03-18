"use client";

import { useState, useMemo, useCallback } from "react";
import type { OccupationSummary, TaskDetail, OccupationTasksResponse } from "@/lib/types";
import { fetchOccupationTasks } from "@/lib/api";

interface Props {
  occupations: OccupationSummary[];
}

// ── Utility formatters ─────────────────────────────────────────────────────────

function fmtEmp(v?: number | null): string {
  if (v == null) return "—";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000)     return `${(v / 1_000).toFixed(0)}K`;
  return v.toLocaleString();
}
function fmtWage(v?: number | null): string {
  if (v == null) return "—";
  return `$${v.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}
function fmtNum(v?: number | null, dec = 2): string {
  if (v == null) return <span style={{ color: "var(--text-muted)", fontStyle: "italic", fontSize: 11 }}>n/a</span> as unknown as string;
  return v.toFixed(dec);
}
function fmtPct(v?: number | null): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

// ── Small badge ────────────────────────────────────────────────────────────────

function Tag({ label, cls }: { label: string; cls: string }) {
  return <span className={`tag ${cls}`}>{label}</span>;
}

// ── Metric cell ────────────────────────────────────────────────────────────────

function MetricCell({ value, dec = 2 }: { value?: number | null; dec?: number }) {
  if (value == null) return <span style={{ color: "var(--text-muted)", fontSize: 11, fontStyle: "italic" }}>n/a</span>;
  return <span>{value.toFixed(dec)}</span>;
}

// ── SVG icon components ────────────────────────────────────────────────────────

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      style={{ color: "var(--text-muted)" }} aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="11" height="11" viewBox="0 0 24 24"
      fill="none" stroke="currentColor"
      strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      style={{
        transform: open ? "rotate(0deg)" : "rotate(-90deg)",
        transition: "transform 0.2s ease",
        flexShrink: 0,
        color: "var(--text-muted)",
      }}
      aria-hidden="true"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

// ── Task row ───────────────────────────────────────────────────────────────────

function TaskRow({ task, aggMode }: { task: TaskDetail; aggMode: "avg" | "max" }) {
  const [expanded, setExpanded] = useState(false);

  const aggAuto = aggMode === "avg" ? task.avg_auto_aug : task.max_auto_aug;
  const aggPct  = aggMode === "avg" ? task.avg_pct_normalized : task.max_pct_normalized;

  const barPct = aggAuto != null ? Math.min(aggAuto / 5, 1) * 100 : null;

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)", transition: "background 0.1s" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "7px 12px", fontSize: 12, color: "var(--text-primary)", maxWidth: 340, verticalAlign: "top" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
            <ChevronIcon open={expanded} />
            <span style={{ lineHeight: 1.4 }}>{task.task}</span>
          </div>
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, color: "var(--text-secondary)", verticalAlign: "top" }}>
          {task.freq_mean?.toFixed(1) ?? "—"}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, color: "var(--text-secondary)", verticalAlign: "top" }}>
          {task.importance?.toFixed(1) ?? "—"}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, color: "var(--text-secondary)", verticalAlign: "top" }}>
          {task.relevance?.toFixed(0) ?? "—"}
        </td>
        <td style={{ padding: "7px 8px", verticalAlign: "top" }}>
          {barPct != null ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 60, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${barPct}%`, height: "100%", background: "var(--brand)", borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{aggAuto?.toFixed(2)}</span>
            </div>
          ) : <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>n/a</span>}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, verticalAlign: "top" }}>
          {aggPct != null
            ? <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtPct(aggPct)}</span>
            : <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>n/a</span>}
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#fafaf8", borderBottom: "1px solid var(--border-light)" }}>
          <td colSpan={6} style={{ padding: "10px 24px 14px" }}>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              {/* GWA/IWA/DWA */}
              <div style={{ minWidth: 220 }}>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Activity Classification</p>
                {task.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {task.gwa_title}</p>}
                {task.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {task.iwa_title}</p>}
                {task.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {task.dwa_title}</p>}
              </div>
              {/* Per-source breakdown */}
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Source Breakdown</p>
                <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ padding: "2px 10px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "left" }}>Source</th>
                      <th style={{ padding: "2px 10px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Auto-aug</th>
                      <th style={{ padding: "2px 10px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Pct Norm</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0" }}><Tag label="AEI" cls="tag-aei" /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        <MetricCell value={task.aei?.auto_aug_mean} />
                      </td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        <MetricCell value={task.aei?.pct_normalized != null ? task.aei.pct_normalized * 100 : null} />
                        {task.aei?.pct_normalized != null && <span style={{ color: "var(--text-muted)" }}>%</span>}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0" }}><Tag label="MCP" cls="tag-mcp" /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        <MetricCell value={task.mcp?.auto_aug_mean_adj} />
                      </td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        <MetricCell value={task.mcp?.pct_normalized != null ? task.mcp.pct_normalized * 100 : null} />
                        {task.mcp?.pct_normalized != null && <span style={{ color: "var(--text-muted)" }}>%</span>}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 10px 2px 0" }}><Tag label="MS" cls="tag-ms" /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        <MetricCell value={task.microsoft?.auto_aug_mean} />
                      </td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        <MetricCell value={task.microsoft?.pct_normalized != null ? task.microsoft.pct_normalized * 100 : null} />
                        {task.microsoft?.pct_normalized != null && <span style={{ color: "var(--text-muted)" }}>%</span>}
                      </td>
                    </tr>
                    <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                      <td style={{ padding: "4px 10px 2px 0", fontWeight: 700 }}>
                        <Tag label={aggMode === "avg" ? "AVG" : "MAX"} cls={aggMode === "avg" ? "tag-avg" : "tag-max"} />
                      </td>
                      <td style={{ padding: "4px 10px 2px", textAlign: "right", fontWeight: 700 }}>
                        <MetricCell value={aggAuto} />
                      </td>
                      <td style={{ padding: "4px 10px 2px", textAlign: "right", fontWeight: 700 }}>
                        <MetricCell value={aggPct != null ? aggPct * 100 : null} />
                        {aggPct != null && <span style={{ color: "var(--text-muted)" }}>%</span>}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Occupation row ─────────────────────────────────────────────────────────────

function OccupationRow({ occ, aggMode, geo }: { occ: OccupationSummary; aggMode: "avg" | "max"; geo: "nat" | "ut" }) {
  const [expanded, setExpanded]   = useState(false);
  const [tasks, setTasks]         = useState<TaskDetail[] | null>(null);
  const [loadingTasks, setLoading] = useState(false);
  const [taskError, setTaskError] = useState<string | null>(null);

  const handleExpand = useCallback(async () => {
    setExpanded((e) => !e);
    if (!tasks && !loadingTasks) {
      setLoading(true);
      try {
        const data: OccupationTasksResponse = await fetchOccupationTasks(occ.title_current);
        setTasks(data.tasks);
      } catch (e: unknown) {
        setTaskError(e instanceof Error ? e.message : "Failed to load tasks");
      } finally {
        setLoading(false);
      }
    }
  }, [occ.title_current, tasks, loadingTasks]);

  const emp  = geo === "nat" ? occ.emp_nat  : occ.emp_ut;
  const wage = geo === "nat" ? occ.wage_nat : occ.wage_ut;

  const avgAuto = [occ.avg_auto_aug_aei, occ.avg_auto_aug_mcp, occ.avg_auto_aug_ms].filter((v) => v != null) as number[];
  const aggAutoVal = avgAuto.length ? (aggMode === "avg" ? avgAuto.reduce((a, b) => a + b, 0) / avgAuto.length : Math.max(...avgAuto)) : null;
  const barPct = aggAutoVal != null ? Math.min(aggAutoVal / 5, 1) * 100 : null;

  return (
    <>
      <tr
        onClick={handleExpand}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)", transition: "background 0.1s" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f5f5f2")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "9px 12px", fontSize: 13, fontWeight: 500, color: "var(--text-primary)", verticalAlign: "top" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <ChevronIcon open={expanded} />
            {occ.title_current}
          </div>
        </td>
        <td style={{ padding: "9px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", whiteSpace: "nowrap" }}>
          {fmtEmp(emp)}
        </td>
        <td style={{ padding: "9px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", whiteSpace: "nowrap" }}>
          {fmtWage(wage)}
        </td>
        <td style={{ padding: "9px 8px", fontSize: 12, color: "var(--text-muted)", textAlign: "center" }}>
          {occ.n_tasks}
        </td>
        <td style={{ padding: "9px 8px" }}>
          {barPct != null ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 56, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${barPct}%`, height: "100%", background: "var(--brand)", borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{aggAutoVal?.toFixed(2)}</span>
            </div>
          ) : <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>—</span>}
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#f7f7f5", borderBottom: "1px solid var(--border)" }}>
          <td colSpan={5} style={{ padding: "0 0 4px 24px" }}>
            {loadingTasks && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "16px 0" }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", border: "2px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading tasks…</span>
              </div>
            )}
            {taskError && (
              <p style={{ fontSize: 12, color: "#b91c1c", padding: "8px 0" }}>Error: {taskError}</p>
            )}
            {tasks && tasks.length > 0 && (
              <div style={{ overflowX: "auto", marginTop: 8, marginRight: 8 }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr style={{ borderBottom: "2px solid var(--border)" }}>
                      <th style={{ padding: "5px 12px 5px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Task</th>
                      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Freq</th>
                      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Imp</th>
                      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Rel</th>
                      <th style={{ padding: "5px 8px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Auto-aug</th>
                      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Pct Norm</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasks.map((t) => <TaskRow key={t.task_normalized} task={t} aggMode={aggMode} />)}
                  </tbody>
                </table>
              </div>
            )}
            {tasks && tasks.length === 0 && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "10px 0" }}>No tasks found for this occupation.</p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

// ── Broad occupation block ────────────────────────────────────────────────────

function BroadBlock({ name, occs, aggMode, geo }: { name: string; occs: OccupationSummary[]; aggMode: "avg" | "max"; geo: "nat" | "ut" }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ marginBottom: 2 }}>
      <button onClick={() => setOpen((o) => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "7px 14px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f2f2ef")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
        <ChevronIcon open={open} />
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>{name}</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>{occs.length} occupation{occs.length !== 1 ? "s" : ""}</span>
      </button>
      <div style={{
        overflow: "hidden",
        maxHeight: open ? "9999px" : "0px",
        opacity: open ? 1 : 0,
        transition: "max-height 0.25s ease, opacity 0.18s ease",
      }}>
        <div style={{ marginLeft: 16 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th style={{ padding: "4px 12px 4px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Occupation</th>
                <th style={{ padding: "4px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Employment</th>
                <th style={{ padding: "4px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Med. Wage</th>
                <th style={{ padding: "4px 8px", textAlign: "center", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Tasks</th>
                <th style={{ padding: "4px 8px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Avg Auto-aug</th>
              </tr>
            </thead>
            <tbody>
              {occs.map((o) => <OccupationRow key={o.title_current} occ={o} aggMode={aggMode} geo={geo} />)}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Minor category block ───────────────────────────────────────────────────────

function MinorBlock({ name, occs, aggMode, geo }: { name: string; occs: OccupationSummary[]; aggMode: "avg" | "max"; geo: "nat" | "ut" }) {
  const [open, setOpen] = useState(false);
  const broadGroups = useMemo(() => {
    const map = new Map<string, OccupationSummary[]>();
    occs.forEach((o) => {
      const k = o.broad ?? "Unknown";
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(o);
    });
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [occs]);

  return (
    <div style={{ marginBottom: 1 }}>
      <button onClick={() => setOpen((o) => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#eeeeea")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
        <ChevronIcon open={open} />
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>{name}</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>{occs.length} occ.</span>
      </button>
      <div style={{
        overflow: "hidden",
        maxHeight: open ? "9999px" : "0px",
        opacity: open ? 1 : 0,
        transition: "max-height 0.25s ease, opacity 0.18s ease",
      }}>
        <div style={{ marginLeft: 12, paddingLeft: 8, borderLeft: "2px solid var(--border-light)" }}>
          {broadGroups.map(([bName, bOccs]) => (
            <BroadBlock key={bName} name={bName} occs={bOccs} aggMode={aggMode} geo={geo} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Major category block ───────────────────────────────────────────────────────

function MajorBlock({ name, occs, aggMode, geo }: { name: string; occs: OccupationSummary[]; aggMode: "avg" | "max"; geo: "nat" | "ut" }) {
  const [open, setOpen] = useState(false);

  const minorGroups = useMemo(() => {
    const map = new Map<string, OccupationSummary[]>();
    occs.forEach((o) => {
      const k = o.minor ?? "Unknown";
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(o);
    });
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [occs]);

  const totalEmp = occs.reduce((s, o) => s + (geo === "nat" ? o.emp_nat ?? 0 : o.emp_ut ?? 0), 0);

  return (
    <div style={{ marginBottom: 4, background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden", boxShadow: "0 1px 2px rgba(0,0,0,0.03)" }}>
      <button onClick={() => setOpen((o) => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "12px 16px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#fafaf7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
        <ChevronIcon open={open} />
        <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>{name}</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
          {occs.length} occupations · {fmtEmp(totalEmp)} workers
        </span>
      </button>
      <div style={{
        overflow: "hidden",
        maxHeight: open ? "9999px" : "0px",
        opacity: open ? 1 : 0,
        transition: "max-height 0.25s ease, opacity 0.18s ease",
      }}>
        <div style={{ borderTop: "1px solid var(--border-light)" }}>
          {minorGroups.map(([mName, mOccs]) => (
            <MinorBlock key={mName} name={mName} occs={mOccs} aggMode={aggMode} geo={geo} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main ExplorerView ─────────────────────────────────────────────────────────

export default function ExplorerView({ occupations }: Props) {
  const [search, setSearch]     = useState("");
  const [selectedMajor, setSelectedMajor] = useState<string | null>(null);
  const [aggMode, setAggMode]   = useState<"avg" | "max">("avg");
  const [geo, setGeo]           = useState<"nat" | "ut">("nat");
  const [searchFocused, setSearchFocused] = useState(false);

  const allMajors = useMemo(() => {
    const s = new Set(occupations.map((o) => o.major ?? "Unknown"));
    return Array.from(s).sort();
  }, [occupations]);

  const filtered = useMemo(() => {
    let list = occupations;
    if (selectedMajor) list = list.filter((o) => o.major === selectedMajor);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((o) => o.title_current.toLowerCase().includes(q) || (o.minor?.toLowerCase().includes(q)) || (o.broad?.toLowerCase().includes(q)));
    }
    return list;
  }, [occupations, selectedMajor, search]);

  const majorGroups = useMemo(() => {
    const map = new Map<string, OccupationSummary[]>();
    filtered.forEach((o) => {
      const k = o.major ?? "Unknown";
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(o);
    });
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [filtered]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - var(--nav-height))", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "0 24px", height: 52, display: "flex", alignItems: "center", gap: 16, flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>Job Explorer</h1>
          <p style={{ fontSize: 11, color: "var(--text-muted)" }}>
            {occupations.length} occupations · click to expand tasks
          </p>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {/* Agg mode */}
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
            {(["avg", "max"] as const).map((m) => (
              <button key={m} onClick={() => setAggMode(m)}
                style={{ padding: "5px 12px", fontSize: 12, fontWeight: m === aggMode ? 700 : 400, background: m === aggMode ? "var(--brand-light)" : "transparent", color: m === aggMode ? "var(--brand)" : "var(--text-secondary)", border: "none", cursor: "pointer", borderRight: m === "avg" ? "1px solid var(--border)" : "none" }}>
                {m === "avg" ? "Average" : "Max"}
              </button>
            ))}
          </div>
          {/* Geo */}
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
            {(["nat", "ut"] as const).map((g) => (
              <button key={g} onClick={() => setGeo(g)}
                style={{ padding: "5px 12px", fontSize: 12, fontWeight: g === geo ? 700 : 400, background: g === geo ? "var(--brand-light)" : "transparent", color: g === geo ? "var(--brand)" : "var(--text-secondary)", border: "none", cursor: "pointer", borderRight: g === "nat" ? "1px solid var(--border)" : "none" }}>
                {g === "nat" ? "National" : "Utah"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Search + filters */}
      <div style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "12px 24px 10px", flexShrink: 0 }}>
        {/* Search */}
        <div style={{ position: "relative", marginBottom: 8 }}>
          <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", display: "flex", alignItems: "center" }}>
            <SearchIcon />
          </span>
          <input
            type="text"
            placeholder="Search occupations…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            style={{
              width: "100%",
              fontSize: 13,
              border: `1px solid ${searchFocused ? "var(--brand)" : "var(--border)"}`,
              borderRadius: 8,
              padding: "8px 12px 8px 32px",
              background: "var(--bg-surface)",
              color: "var(--text-primary)",
              outline: "none",
              boxSizing: "border-box",
              boxShadow: searchFocused ? "0 0 0 2px var(--brand-light)" : "none",
              transition: "border-color 0.15s ease, box-shadow 0.15s ease",
            }}
          />
          {search && (
            <button onClick={() => setSearch("")}
              style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: 16 }}>
              ×
            </button>
          )}
        </div>
        {/* Major category chips */}
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <button
            onClick={() => setSelectedMajor(null)}
            className={`filter-chip${!selectedMajor ? " selected" : ""}`}>
            All ({occupations.length})
          </button>
          {allMajors.map((m) => {
            const cnt = occupations.filter((o) => o.major === m).length;
            return (
              <button key={m}
                onClick={() => setSelectedMajor(selectedMajor === m ? null : m)}
                className={`filter-chip${selectedMajor === m ? " selected" : ""}`}>
                {m} ({cnt})
              </button>
            );
          })}
        </div>
      </div>

      {/* Results */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 24px" }}>
        {filtered.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200, fontSize: 13, color: "var(--text-muted)" }}>
            No occupations match your search.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {majorGroups.map(([mName, mOccs]) => (
              <MajorBlock key={mName} name={mName} occs={mOccs} aggMode={aggMode} geo={geo} />
            ))}
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
