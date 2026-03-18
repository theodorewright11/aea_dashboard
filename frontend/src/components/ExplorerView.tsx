"use client";

import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import type { OccupationSummary, TaskDetail, OccupationTasksResponse, ConfigResponse, ChartRow } from "@/lib/types";
import { fetchOccupationTasks, fetchCompute } from "@/lib/api";

interface Props { occupations: OccupationSummary[]; config: ConfigResponse }

// ── Formatters ────────────────────────────────────────────────────────────────

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
function fmtPct(v?: number | null): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

// ── Auto-aug helpers ──────────────────────────────────────────────────────────

function getAutoAug(occ: OccupationSummary, aggMode: "avg" | "max"): number | null {
  const vals = [occ.avg_auto_aug_aei, occ.avg_auto_aug_mcp, occ.avg_auto_aug_ms].filter((v) => v != null) as number[];
  if (!vals.length) return null;
  return aggMode === "max" ? Math.max(...vals) : vals.reduce((a, b) => a + b, 0) / vals.length;
}

// ── Flat table aggregation ────────────────────────────────────────────────────

interface FlatRow {
  name: string;
  emp: number;
  wage: number | null;
  n_occs: number;
  n_tasks: number;
  avg_auto_aug: number | null;
  sourceOccs: OccupationSummary[];
}

function aggregateOccs(occs: OccupationSummary[], geo: "nat" | "ut", aggMode: "avg" | "max"): Omit<FlatRow, "name" | "sourceOccs"> {
  let totalEmp = 0, wageSum = 0, wageTotalEmp = 0, totalTasks = 0;
  const autoAugs: number[] = [];
  occs.forEach((occ) => {
    const emp  = (geo === "nat" ? occ.emp_nat  : occ.emp_ut)  ?? 0;
    const wage = (geo === "nat" ? occ.wage_nat : occ.wage_ut) ?? null;
    totalEmp  += emp;
    totalTasks += occ.n_tasks;
    if (wage != null && emp > 0) { wageSum += wage * emp; wageTotalEmp += emp; }
    const aa = getAutoAug(occ, aggMode);
    if (aa != null) autoAugs.push(aa);
  });
  return {
    emp:  totalEmp,
    wage: wageTotalEmp > 0 ? wageSum / wageTotalEmp : null,
    n_occs: occs.length,
    n_tasks: totalTasks,
    avg_auto_aug: autoAugs.length
      ? (aggMode === "max" ? Math.max(...autoAugs) : autoAugs.reduce((a, b) => a + b, 0) / autoAugs.length)
      : null,
  };
}

// ── SVG icons ─────────────────────────────────────────────────────────────────

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
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: open ? "rotate(0deg)" : "rotate(-90deg)", transition: "transform 0.2s ease", flexShrink: 0, color: "var(--text-muted)" }}
      aria-hidden="true">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

// ── Info tooltip ──────────────────────────────────────────────────────────────

function InfoTooltip({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  return (
    <span style={{ position: "relative", display: "inline-flex", alignItems: "center", marginLeft: 3 }}>
      <span
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        style={{
          cursor: "help", color: "var(--text-muted)", fontSize: 9, fontWeight: 700,
          border: "1px solid var(--border)", borderRadius: "50%",
          width: 12, height: 12, display: "inline-flex", alignItems: "center", justifyContent: "center",
          lineHeight: 1, userSelect: "none",
        }}
      >?</span>
      {show && (
        <div style={{
          position: "absolute", bottom: "calc(100% + 4px)", left: "50%", transform: "translateX(-50%)",
          background: "#1a1a1a", color: "#fff", fontSize: 11, padding: "6px 10px",
          borderRadius: 6, whiteSpace: "nowrap", zIndex: 200, pointerEvents: "none",
          boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
        }}>
          {text}
        </div>
      )}
    </span>
  );
}

function Tag({ label, cls }: { label: string; cls: string }) {
  return <span className={`tag ${cls}`}>{label}</span>;
}

function MetricCell({ value, dec = 2 }: { value?: number | null; dec?: number }) {
  if (value == null) return <span style={{ color: "var(--text-muted)", fontSize: 11, fontStyle: "italic" }}>n/a</span>;
  return <span>{value.toFixed(dec)}</span>;
}

// ── Task row ──────────────────────────────────────────────────────────────────

function TaskRow({ task, aggMode, physicalMode }: {
  task: TaskDetail;
  aggMode: "avg" | "max";
  physicalMode: "all" | "exclude" | "only";
}) {
  const [expanded, setExpanded] = useState(false);
  const aggAuto = aggMode === "avg" ? task.avg_auto_aug : task.max_auto_aug;
  const aggPct  = aggMode === "avg" ? task.avg_pct_normalized : task.max_pct_normalized;
  const barPct  = aggAuto != null ? Math.min(aggAuto / 5, 1) * 100 : null;

  // Physical filter at task level
  if (physicalMode === "exclude" && task.physical === true) return null;
  if (physicalMode === "only"    && task.physical !== true) return null;

  return (
    <>
      <tr
        onClick={() => setExpanded((e) => !e)}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)", transition: "background 0.1s" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "7px 12px", fontSize: 12, color: "var(--text-primary)", verticalAlign: "top" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
            <ChevronIcon open={expanded} />
            <span style={{ lineHeight: 1.4 }}>{task.task}</span>
          </div>
        </td>
        <td style={{ padding: "7px 8px", textAlign: "center", verticalAlign: "top", width: 52 }}>
          {task.physical === true
            ? <span style={{ color: "#16a34a", fontSize: 12 }}>✓</span>
            : task.physical === false
            ? <span style={{ color: "var(--text-muted)", fontSize: 12 }}>✗</span>
            : <span style={{ color: "var(--text-muted)", fontSize: 11, fontStyle: "italic" }}>—</span>}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", verticalAlign: "top", width: 56 }}>
          {task.freq_mean?.toFixed(1) ?? "—"}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", verticalAlign: "top", width: 56 }}>
          {task.importance?.toFixed(1) ?? "—"}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", verticalAlign: "top", width: 56 }}>
          {task.relevance?.toFixed(0) ?? "—"}
        </td>
        <td style={{ padding: "7px 8px", verticalAlign: "top", width: 110 }}>
          {barPct != null ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 56, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden", flexShrink: 0 }}>
                <div style={{ width: `${barPct}%`, height: "100%", background: "var(--brand)", borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{aggAuto?.toFixed(2)}</span>
            </div>
          ) : <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>n/a</span>}
        </td>
        <td style={{ padding: "7px 8px", fontSize: 12, textAlign: "right", verticalAlign: "top", width: 80 }}>
          {aggPct != null
            ? <span style={{ color: "var(--brand)", fontWeight: 500 }}>{fmtPct(aggPct)}</span>
            : <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>n/a</span>}
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#fafaf8", borderBottom: "1px solid var(--border-light)" }}>
          <td colSpan={7} style={{ padding: "10px 24px 14px" }}>
            <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
              <div style={{ minWidth: 220 }}>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Activity Classification</p>
                {task.gwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>GWA:</b> {task.gwa_title}</p>}
                {task.iwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)", marginBottom: 2 }}><b>IWA:</b> {task.iwa_title}</p>}
                {task.dwa_title && <p style={{ fontSize: 11, color: "var(--text-secondary)" }}><b>DWA:</b> {task.dwa_title}</p>}
              </div>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 6 }}>Source Breakdown</p>
                <table style={{ fontSize: 11, borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ padding: "2px 12px 2px 0", color: "var(--text-muted)", fontWeight: 600, textAlign: "left" }}>Source</th>
                      <th style={{ padding: "2px 10px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Auto-aug</th>
                      <th style={{ padding: "2px 10px", color: "var(--text-muted)", fontWeight: 600, textAlign: "right" }}>Pct Norm</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ padding: "2px 12px 2px 0" }}><Tag label="AEI" cls="tag-aei" /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}><MetricCell value={task.aei?.auto_aug_mean} /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        {task.aei?.pct_normalized != null
                          ? <>{(task.aei.pct_normalized * 100).toFixed(2)}<span style={{ color: "var(--text-muted)" }}>%</span></>
                          : <MetricCell value={null} />}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 12px 2px 0" }}><Tag label="MCP" cls="tag-mcp" /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}><MetricCell value={task.mcp?.auto_aug_mean_adj} /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        {task.mcp?.pct_normalized != null
                          ? <>{(task.mcp.pct_normalized * 100).toFixed(2)}<span style={{ color: "var(--text-muted)" }}>%</span></>
                          : <MetricCell value={null} />}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ padding: "2px 12px 2px 0" }}><Tag label="MS" cls="tag-ms" /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}><MetricCell value={task.microsoft?.auto_aug_mean} /></td>
                      <td style={{ padding: "2px 10px", textAlign: "right" }}>
                        {task.microsoft?.pct_normalized != null
                          ? <>{(task.microsoft.pct_normalized * 100).toFixed(2)}<span style={{ color: "var(--text-muted)" }}>%</span></>
                          : <MetricCell value={null} />}
                      </td>
                    </tr>
                    <tr style={{ borderTop: "1px solid var(--border-light)" }}>
                      <td style={{ padding: "4px 12px 2px 0", fontWeight: 700 }}>
                        <Tag label={aggMode === "avg" ? "AVG" : "MAX"} cls={aggMode === "avg" ? "tag-avg" : "tag-max"} />
                      </td>
                      <td style={{ padding: "4px 10px 2px", textAlign: "right", fontWeight: 700 }}><MetricCell value={aggAuto} /></td>
                      <td style={{ padding: "4px 10px 2px", textAlign: "right", fontWeight: 700 }}>
                        {aggPct != null
                          ? <>{(aggPct * 100).toFixed(2)}<span style={{ color: "var(--text-muted)" }}>%</span></>
                          : <MetricCell value={null} />}
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

// ── Task table header ─────────────────────────────────────────────────────────

function TaskTableHeader() {
  return (
    <tr style={{ borderBottom: "2px solid var(--border)" }}>
      <th style={{ padding: "5px 12px 5px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Task</th>
      <th style={{ padding: "5px 8px", textAlign: "center", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 52 }}>
        Phys<InfoTooltip text="Physical task (truly requires physical presence)" />
      </th>
      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 56, whiteSpace: "nowrap" }}>
        Freq<InfoTooltip text="O*NET frequency rating (0–10). How often workers perform this task." />
      </th>
      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 56, whiteSpace: "nowrap" }}>
        Imp<InfoTooltip text="O*NET importance rating (0–5). How critical this task is to the job." />
      </th>
      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 56, whiteSpace: "nowrap" }}>
        Rel<InfoTooltip text="O*NET relevance score (0–100). Overall relevance weighting." />
      </th>
      <th style={{ padding: "5px 8px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 110, whiteSpace: "nowrap" }}>
        Auto-aug<InfoTooltip text="AI automatability score (0–5, averaged across sources). Higher = more automatable." />
      </th>
      <th style={{ padding: "5px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", width: 80, whiteSpace: "nowrap" }}>
        Pct Norm<InfoTooltip text="Share of AI conversations referencing this task. From AI datasets only." />
      </th>
    </tr>
  );
}

// ── Occupation row (accordion) ─────────────────────────────────────────────────

function OccupationRow({
  occ, aggMode, geo, physicalMode, autoAugMin,
}: {
  occ: OccupationSummary;
  aggMode: "avg" | "max";
  geo: "nat" | "ut";
  physicalMode: "all" | "exclude" | "only";
  autoAugMin: number;
}) {
  const [expanded, setExpanded]   = useState(false);
  const [tasks,    setTasks]      = useState<TaskDetail[] | null>(null);
  const [loadingT, setLoadingT]   = useState(false);
  const [taskErr,  setTaskErr]    = useState<string | null>(null);

  const handleExpand = useCallback(async () => {
    setExpanded((e) => !e);
    if (!tasks && !loadingT) {
      setLoadingT(true);
      try {
        const data: OccupationTasksResponse = await fetchOccupationTasks(occ.title_current);
        setTasks(data.tasks);
      } catch (e: unknown) {
        setTaskErr(e instanceof Error ? e.message : "Failed to load tasks");
      } finally { setLoadingT(false); }
    }
  }, [occ.title_current, tasks, loadingT]);

  const emp  = geo === "nat" ? occ.emp_nat  : occ.emp_ut;
  const wage = geo === "nat" ? occ.wage_nat : occ.wage_ut;

  const aggAutoVal = getAutoAug(occ, aggMode);
  const barPct = aggAutoVal != null ? Math.min(aggAutoVal / 5, 1) * 100 : null;

  // Filter by auto-aug threshold
  if (autoAugMin > 0 && (aggAutoVal == null || aggAutoVal < autoAugMin)) return null;

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
        <td style={{ padding: "9px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", whiteSpace: "nowrap" }}>{fmtEmp(emp)}</td>
        <td style={{ padding: "9px 8px", fontSize: 12, color: "var(--text-secondary)", textAlign: "right", whiteSpace: "nowrap" }}>{fmtWage(wage)}</td>
        <td style={{ padding: "9px 8px", fontSize: 12, color: "var(--text-muted)", textAlign: "center" }}>{occ.n_tasks}</td>
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
            {loadingT && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "16px 0" }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", border: "2px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading tasks…</span>
              </div>
            )}
            {taskErr && <p style={{ fontSize: 12, color: "#b91c1c", padding: "8px 0" }}>Error: {taskErr}</p>}
            {tasks && tasks.length > 0 && (
              <div style={{ overflowX: "auto", marginTop: 8, marginRight: 8 }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead><TaskTableHeader /></thead>
                  <tbody>
                    {tasks.map((t) => (
                      <TaskRow
                        key={t.task_normalized}
                        task={t}
                        aggMode={aggMode}
                        physicalMode={physicalMode}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {tasks && tasks.length === 0 && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "10px 0" }}>No tasks found.</p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

// ── Broad block ───────────────────────────────────────────────────────────────

function BroadBlock({ name, occs, aggMode, geo, autoOpen, physicalMode, autoAugMin }: {
  name: string; occs: OccupationSummary[]; aggMode: "avg" | "max"; geo: "nat" | "ut"; autoOpen: boolean;
  physicalMode: "all" | "exclude" | "only"; autoAugMin: number;
}) {
  const [open, setOpen] = useState(autoOpen);
  useEffect(() => { setOpen(autoOpen); }, [autoOpen]);

  return (
    <div style={{ marginBottom: 2 }}>
      <button onClick={() => setOpen((o) => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "7px 14px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f2f2ef")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
        <ChevronIcon open={open} />
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>{name}</span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>{occs.length} occ.</span>
      </button>
      <div style={{ overflow: "hidden", maxHeight: open ? "9999px" : "0px", opacity: open ? 1 : 0, transition: "max-height 0.25s ease, opacity 0.18s ease" }}>
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
              {occs.map((o) => (
                <OccupationRow
                  key={o.title_current} occ={o} aggMode={aggMode} geo={geo}
                  physicalMode={physicalMode} autoAugMin={autoAugMin}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Minor block ───────────────────────────────────────────────────────────────

function MinorBlock({ name, occs, aggMode, geo, autoOpen, physicalMode, autoAugMin }: {
  name: string; occs: OccupationSummary[]; aggMode: "avg" | "max"; geo: "nat" | "ut"; autoOpen: boolean;
  physicalMode: "all" | "exclude" | "only"; autoAugMin: number;
}) {
  const [open, setOpen] = useState(autoOpen);
  useEffect(() => { setOpen(autoOpen); }, [autoOpen]);

  const broadGroups = useMemo(() => {
    const map = new Map<string, OccupationSummary[]>();
    occs.forEach((o) => { const k = o.broad ?? "Unknown"; if (!map.has(k)) map.set(k, []); map.get(k)!.push(o); });
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
      <div style={{ overflow: "hidden", maxHeight: open ? "9999px" : "0px", opacity: open ? 1 : 0, transition: "max-height 0.25s ease, opacity 0.18s ease" }}>
        <div style={{ marginLeft: 12, paddingLeft: 8, borderLeft: "2px solid var(--border-light)" }}>
          {broadGroups.map(([bName, bOccs]) => (
            <BroadBlock
              key={bName} name={bName} occs={bOccs} aggMode={aggMode} geo={geo} autoOpen={autoOpen}
              physicalMode={physicalMode} autoAugMin={autoAugMin}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Major block ───────────────────────────────────────────────────────────────

function MajorBlock({ name, occs, aggMode, geo, autoOpen, physicalMode, autoAugMin }: {
  name: string; occs: OccupationSummary[]; aggMode: "avg" | "max"; geo: "nat" | "ut"; autoOpen: boolean;
  physicalMode: "all" | "exclude" | "only"; autoAugMin: number;
}) {
  const [open, setOpen] = useState(autoOpen);
  useEffect(() => { setOpen(autoOpen); }, [autoOpen]);

  const minorGroups = useMemo(() => {
    const map = new Map<string, OccupationSummary[]>();
    occs.forEach((o) => { const k = o.minor ?? "Unknown"; if (!map.has(k)) map.set(k, []); map.get(k)!.push(o); });
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [occs]);

  const totalEmp = occs.reduce((s, o) => s + ((geo === "nat" ? o.emp_nat : o.emp_ut) ?? 0), 0);

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
      <div style={{ overflow: "hidden", maxHeight: open ? "9999px" : "0px", opacity: open ? 1 : 0, transition: "max-height 0.25s ease, opacity 0.18s ease" }}>
        <div style={{ borderTop: "1px solid var(--border-light)" }}>
          {minorGroups.map(([mName, mOccs]) => (
            <MinorBlock
              key={mName} name={mName} occs={mOccs} aggMode={aggMode} geo={geo} autoOpen={autoOpen}
              physicalMode={physicalMode} autoAugMin={autoAugMin}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Flat table — drilldown row ─────────────────────────────────────────────────

type TableLevel = "major" | "minor" | "broad" | "occupation";
const LEVEL_ORDER: TableLevel[] = ["major", "minor", "broad", "occupation"];

function nextLevel(level: TableLevel): TableLevel | null {
  const idx = LEVEL_ORDER.indexOf(level);
  return idx < LEVEL_ORDER.length - 1 ? LEVEL_ORDER[idx + 1] : null;
}

interface DrilldownRowProps {
  row: FlatRow;
  level: TableLevel;
  geo: "nat" | "ut";
  aggMode: "avg" | "max";
  autoAugMin: number;
  minEmp: number;
  minWage: number;
  pctAffectedMap: Map<string, number> | null;
  minPctAffected: number;
  physicalMode: "all" | "exclude" | "only";
  indent: number;
  showOccsCol: boolean;
}

function DrilldownRow({
  row, level, geo, aggMode, autoAugMin, minEmp, minWage,
  pctAffectedMap, minPctAffected, physicalMode, indent, showOccsCol,
}: DrilldownRowProps) {
  const [open,      setOpen]      = useState(false);
  const [tasks,     setTasks]     = useState<TaskDetail[] | null>(null);
  const [loadingT,  setLoadingT]  = useState(false);
  const [taskErr,   setTaskErr]   = useState<string | null>(null);

  const isOccupation = level === "occupation";
  const child = nextLevel(level);

  const pct = pctAffectedMap?.get(row.name);

  // Hooks must all come before any conditional return
  const handleClick = useCallback(async () => {
    setOpen((o) => !o);
    if (isOccupation && !tasks && !loadingT) {
      setLoadingT(true);
      try {
        const data: OccupationTasksResponse = await fetchOccupationTasks(row.name);
        setTasks(data.tasks);
      } catch (e: unknown) {
        setTaskErr(e instanceof Error ? e.message : "Failed to load tasks");
      } finally { setLoadingT(false); }
    }
  }, [isOccupation, row.name, tasks, loadingT]);

  const barPct = row.avg_auto_aug != null ? Math.min(row.avg_auto_aug / 5, 1) * 100 : null;
  const indentPx = indent * 20;

  // Build child rows from source occupations
  const childRows = useMemo<FlatRow[]>(() => {
    if (!open || isOccupation || !child) return [];
    if (child === "occupation") {
      return row.sourceOccs.map((occ) => ({
        name: occ.title_current,
        emp:  (geo === "nat" ? occ.emp_nat  : occ.emp_ut)  ?? 0,
        wage: (geo === "nat" ? occ.wage_nat : occ.wage_ut) ?? null,
        n_occs: 1,
        n_tasks: occ.n_tasks,
        avg_auto_aug: getAutoAug(occ, aggMode),
        sourceOccs: [occ],
      })).sort((a, b) => b.emp - a.emp);
    }
    const map = new Map<string, OccupationSummary[]>();
    row.sourceOccs.forEach((occ) => {
      const k = occ[child] ?? "Unknown";
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(occ);
    });
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([name, occs]) => ({ name, ...aggregateOccs(occs, geo, aggMode), sourceOccs: occs }))
      .sort((a, b) => b.emp - a.emp);
  }, [open, isOccupation, child, row.sourceOccs, geo, aggMode]);

  // Apply filters after all hooks
  if (autoAugMin > 0 && (row.avg_auto_aug == null || row.avg_auto_aug < autoAugMin)) return null;
  if (minEmp  > 0 && row.emp < minEmp)  return null;
  if (minWage > 0 && (row.wage == null || row.wage < minWage)) return null;
  if (minPctAffected > 0 && (pct == null || pct < minPctAffected)) return null;

  return (
    <>
      <tr
        onClick={handleClick}
        style={{ cursor: "pointer", borderBottom: "1px solid var(--border-light)", transition: "background 0.1s" }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#f9f9f7")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <td style={{ padding: "8px 12px", fontSize: 13, color: "var(--text-primary)", fontWeight: indent === 0 ? 600 : indent === 1 ? 500 : 400 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, paddingLeft: indentPx }}>
            <ChevronIcon open={open} />
            {row.name}
          </div>
        </td>
        <td style={{ padding: "8px 8px", textAlign: "right", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>{fmtEmp(row.emp)}</td>
        <td style={{ padding: "8px 8px", textAlign: "right", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>{fmtWage(row.wage)}</td>
        {showOccsCol && <td style={{ padding: "8px 8px", textAlign: "right", color: "var(--text-muted)" }}>{level === "occupation" ? "—" : row.n_occs}</td>}
        <td style={{ padding: "8px 8px", textAlign: "right", color: "var(--text-muted)" }}>{row.n_tasks}</td>
        <td style={{ padding: "8px 8px" }}>
          {barPct != null ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 56, height: 6, background: "var(--border)", borderRadius: 3, overflow: "hidden", flexShrink: 0 }}>
                <div style={{ width: `${barPct}%`, height: "100%", background: "var(--brand)", borderRadius: 3 }} />
              </div>
              <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>{row.avg_auto_aug?.toFixed(2)}</span>
            </div>
          ) : <span style={{ fontSize: 11, color: "var(--text-muted)", fontStyle: "italic" }}>—</span>}
        </td>
        {pctAffectedMap && (
          <td style={{ padding: "8px 8px", textAlign: "right", color: pct != null ? "var(--brand)" : "var(--text-muted)", fontWeight: pct != null ? 500 : 400 }}>
            {pct != null ? `${pct.toFixed(1)}%` : "—"}
          </td>
        )}
      </tr>

      {/* Child rows (non-occupation) */}
      {open && !isOccupation && childRows.map((cr) => (
        <DrilldownRow
          key={cr.name}
          row={cr} level={child!} geo={geo} aggMode={aggMode}
          autoAugMin={autoAugMin} minEmp={minEmp} minWage={minWage}
          pctAffectedMap={pctAffectedMap} minPctAffected={minPctAffected}
          physicalMode={physicalMode} indent={indent + 1} showOccsCol={showOccsCol}
        />
      ))}

      {/* Task rows (occupation) */}
      {open && isOccupation && (
        <tr style={{ background: "#f7f7f5", borderBottom: "1px solid var(--border)" }}>
          <td colSpan={pctAffectedMap ? (showOccsCol ? 7 : 6) : (showOccsCol ? 6 : 5)} style={{ padding: "0 0 4px", paddingLeft: indentPx + 28 }}>
            {loadingT && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 0" }}>
                <div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading tasks…</span>
              </div>
            )}
            {taskErr && <p style={{ fontSize: 12, color: "#b91c1c", padding: "8px 0" }}>{taskErr}</p>}
            {tasks && tasks.length > 0 && (
              <div style={{ overflowX: "auto", marginTop: 8, marginRight: 8 }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead><TaskTableHeader /></thead>
                  <tbody>
                    {tasks.map((t) => (
                      <TaskRow key={t.task_normalized} task={t} aggMode={aggMode} physicalMode={physicalMode} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {tasks && tasks.length === 0 && (
              <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "8px 0" }}>No tasks found.</p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

// ── Flat table view ───────────────────────────────────────────────────────────

function FlatTable({
  occupations, geo, aggMode, tableLevel, autoAugMin, minEmp, minWage,
  pctAffectedMap, minPctAffected, physicalMode,
}: {
  occupations: OccupationSummary[];
  geo: "nat" | "ut";
  aggMode: "avg" | "max";
  tableLevel: TableLevel;
  autoAugMin: number;
  minEmp: number;
  minWage: number;
  pctAffectedMap: Map<string, number> | null;
  minPctAffected: number;
  physicalMode: "all" | "exclude" | "only";
}) {
  const rows = useMemo<FlatRow[]>(() => {
    if (tableLevel === "occupation") {
      return occupations
        .map((occ) => ({
          name: occ.title_current,
          emp:  (geo === "nat" ? occ.emp_nat  : occ.emp_ut)  ?? 0,
          wage: (geo === "nat" ? occ.wage_nat : occ.wage_ut) ?? null,
          n_occs: 1,
          n_tasks: occ.n_tasks,
          avg_auto_aug: getAutoAug(occ, aggMode),
          sourceOccs: [occ],
        }))
        .sort((a, b) => b.emp - a.emp);
    }
    const map = new Map<string, OccupationSummary[]>();
    occupations.forEach((occ) => {
      const k = occ[tableLevel] ?? "Unknown";
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(occ);
    });
    return Array.from(map.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([name, occs]) => ({ name, ...aggregateOccs(occs, geo, aggMode), sourceOccs: occs }))
      .sort((a, b) => b.emp - a.emp);
  }, [occupations, geo, tableLevel, aggMode]);

  const showOccsCol  = tableLevel !== "occupation";
  const hasPct = pctAffectedMap != null;

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: "2px solid var(--border)" }}>
            <th style={{ padding: "7px 12px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              {tableLevel.charAt(0).toUpperCase() + tableLevel.slice(1)}
            </th>
            <th style={{ padding: "7px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Employment</th>
            <th style={{ padding: "7px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Med. Wage</th>
            {showOccsCol && (
              <th style={{ padding: "7px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}># Occs</th>
            )}
            <th style={{ padding: "7px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>Tasks</th>
            <th style={{ padding: "7px 8px", textAlign: "left", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
              {aggMode === "max" ? "Max" : "Avg"} Auto-aug<InfoTooltip text="AI automatability score (0–5). Aggregated across AEI, MCP, and Microsoft sources." />
            </th>
            {hasPct && (
              <th style={{ padding: "7px 8px", textAlign: "right", fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", whiteSpace: "nowrap" }}>
                % Tasks Affected<InfoTooltip text="Share of task completion attributable to AI-automatable tasks, using the selected compute settings." />
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <DrilldownRow
              key={row.name}
              row={row} level={tableLevel} geo={geo} aggMode={aggMode}
              autoAugMin={autoAugMin} minEmp={minEmp} minWage={minWage}
              pctAffectedMap={pctAffectedMap} minPctAffected={minPctAffected}
              physicalMode={physicalMode} indent={0} showOccsCol={showOccsCol}
            />
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={hasPct ? (showOccsCol ? 7 : 6) : (showOccsCol ? 6 : 5)}
                style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
                No rows match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── % Tasks Affected compute panel ────────────────────────────────────────────

interface PctSettings {
  datasets:     string[];
  combineMethod: "Average" | "Max";
  method:       "freq" | "imp";
  geo:          "nat" | "ut";
  physicalMode: "all" | "exclude" | "only";
  useAutoAug:   boolean;
  useAdjMean:   boolean;
}

function PctComputePanel({
  config, geo, onResult,
}: {
  config: ConfigResponse;
  geo: "nat" | "ut";
  onResult: (map: Map<string, number> | null) => void;
}) {
  const [open,    setOpen]    = useState(false);
  const [settings, setSettings] = useState<PctSettings>({
    datasets: ["AEI v4"], combineMethod: "Average", method: "freq", geo,
    physicalMode: "all", useAutoAug: false, useAdjMean: false,
  });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const [computed, setComputed] = useState(false);

  // Sync geo from parent
  useEffect(() => { setSettings((s) => ({ ...s, geo })); }, [geo]);

  function set<K extends keyof PctSettings>(k: K, v: PctSettings[K]) {
    setSettings((s) => ({ ...s, [k]: v }));
  }

  const hasMCP = settings.datasets.some((d) => d.startsWith("MCP"));

  const compute = useCallback(async () => {
    if (!settings.datasets.length) return;
    setLoading(true); setError(null);
    try {
      const resp = await fetchCompute({
        selectedDatasets: settings.datasets,
        combineMethod:    settings.combineMethod,
        method:           settings.method,
        useAutoAug:       settings.useAutoAug,
        useAdjMean:       settings.useAutoAug && settings.useAdjMean,
        physicalMode:     settings.physicalMode,
        geo:              settings.geo,
        aggLevel:         "occupation",
        sortBy:           "Workers Affected",
        topN:             1000,
        searchQuery:      "",
        contextSize:      5,
      });
      const map = new Map<string, number>();
      resp.rows.forEach((r: ChartRow) => map.set(r.category, r.pct_tasks_affected));
      onResult(map);
      setComputed(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Compute failed");
    } finally { setLoading(false); }
  }, [settings, onResult]);

  const BtnSeg = ({ opts, val, onChange }: { opts: {v: string; l: string}[]; val: string; onChange: (v: string) => void }) => (
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

  return (
    <div style={{ marginTop: 10, border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        style={{ width: "100%", display: "flex", alignItems: "center", gap: 8, padding: "8px 14px", background: open ? "var(--brand-light)" : "var(--bg-surface)", border: "none", cursor: "pointer", textAlign: "left" }}
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
            {/* Dataset multiselect */}
            <div>
              <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Datasets</p>
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap", maxWidth: 400 }}>
                {config.datasets.map((ds) => {
                  const avail = config.dataset_availability[ds];
                  const sel   = settings.datasets.includes(ds);
                  return (
                    <button key={ds} disabled={!avail} onClick={() => {
                      const next = sel ? settings.datasets.filter((d) => d !== ds) : [...settings.datasets, ds];
                      set("datasets", next);
                    }} style={{
                      fontSize: 10, padding: "3px 7px", borderRadius: 5,
                      border: `1.5px solid ${sel ? "var(--brand)" : "var(--border)"}`,
                      background: sel ? "var(--brand-light)" : "transparent",
                      color: sel ? "var(--brand)" : avail ? "var(--text-secondary)" : "var(--text-muted)",
                      cursor: avail ? "pointer" : "default", fontWeight: sel ? 600 : 400,
                      textDecoration: avail ? "none" : "line-through",
                    }}>{ds}</button>
                  );
                })}
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Method</p>
                <BtnSeg opts={[{v:"freq",l:"Freq"},{v:"imp",l:"Imp"}]} val={settings.method} onChange={(v) => set("method", v as "freq"|"imp")} />
              </div>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Physical</p>
                <BtnSeg opts={[{v:"all",l:"All"},{v:"exclude",l:"No Phys"},{v:"only",l:"Phys only"}]} val={settings.physicalMode} onChange={(v) => set("physicalMode", v as "all"|"exclude"|"only")} />
              </div>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>Auto-aug</p>
                <BtnSeg opts={[{v:"false",l:"Off"},{v:"true",l:"On"}]} val={String(settings.useAutoAug)} onChange={(v) => set("useAutoAug", v === "true")} />
              </div>
              {hasMCP && settings.useAutoAug && (
                <div>
                  <p style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 4px" }}>MCP adj mean</p>
                  <BtnSeg opts={[{v:"false",l:"Off"},{v:"true",l:"On"}]} val={String(settings.useAdjMean)} onChange={(v) => set("useAdjMean", v === "true")} />
                </div>
              )}
              <button
                onClick={compute} disabled={loading || !settings.datasets.length}
                className="btn-brand" style={{ padding: "6px 18px", fontSize: 12, opacity: loading || !settings.datasets.length ? 0.5 : 1 }}
              >
                {loading ? "Computing…" : "Compute %"}
              </button>
            </div>
          </div>
          {error && <p style={{ fontSize: 11, color: "#b91c1c", margin: 0 }}>Error: {error}</p>}
          {computed && <p style={{ fontSize: 11, color: "#16a34a", margin: 0 }}>% Tasks Affected computed — use the slider below to filter rows.</p>}
        </div>
      )}
    </div>
  );
}

// ── Main ExplorerView ─────────────────────────────────────────────────────────

export default function ExplorerView({ occupations, config }: Props) {
  const [search,        setSearch]        = useState("");
  const [selectedMajor, setSelectedMajor] = useState<string | null>(null);
  const [aggMode,       setAggMode]       = useState<"avg" | "max">("avg");
  const [geo,           setGeo]           = useState<"nat" | "ut">("nat");
  const [viewMode,      setViewMode]      = useState<"accordion" | "table">("accordion");
  const [tableLevel,    setTableLevel]    = useState<TableLevel>("major");
  const [autoAugMin,    setAutoAugMin]    = useState(0);
  const [minEmp,        setMinEmp]        = useState(0);
  const [minWage,       setMinWage]       = useState(0);
  const [physicalMode,  setPhysicalMode]  = useState<"all" | "exclude" | "only">("all");
  const [searchFocused, setSearchFocused] = useState(false);

  // % Tasks Affected
  const [pctAffectedMap,  setPctAffectedMap]  = useState<Map<string, number> | null>(null);
  const [minPctAffected,  setMinPctAffected]  = useState(0);

  const searchActive = search.trim().length > 0;

  const allMajors = useMemo(() => {
    const s = new Set(occupations.map((o) => o.major ?? "Unknown"));
    return Array.from(s).sort();
  }, [occupations]);

  const filtered = useMemo(() => {
    let list = occupations;
    if (selectedMajor) list = list.filter((o) => o.major === selectedMajor);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((o) =>
        o.title_current.toLowerCase().includes(q) ||
        (o.minor?.toLowerCase().includes(q)) ||
        (o.broad?.toLowerCase().includes(q))
      );
    }
    return list;
  }, [occupations, selectedMajor, search]);

  const majorGroups = useMemo(() => {
    const map = new Map<string, OccupationSummary[]>();
    filtered.forEach((o) => { const k = o.major ?? "Unknown"; if (!map.has(k)) map.set(k, []); map.get(k)!.push(o); });
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [filtered]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - var(--nav-height))", overflow: "hidden" }}>

      {/* ── Header ── */}
      <div style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "0 24px", height: 52, display: "flex", alignItems: "center", gap: 16, flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>Job Explorer</h1>
          <p style={{ fontSize: 11, color: "var(--text-muted)" }}>{occupations.length} occupations</p>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, alignItems: "center" }}>
          {/* View toggle */}
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
            {(["accordion", "table"] as const).map((m, i) => (
              <button key={m} onClick={() => setViewMode(m)}
                style={{ padding: "5px 12px", fontSize: 12, fontWeight: m === viewMode ? 700 : 400, background: m === viewMode ? "var(--brand-light)" : "transparent", color: m === viewMode ? "var(--brand)" : "var(--text-secondary)", border: "none", cursor: "pointer", borderRight: i === 0 ? "1px solid var(--border)" : "none" }}>
                {m === "accordion" ? "Accordion" : "Table"}
              </button>
            ))}
          </div>
          {/* Agg mode */}
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
            {(["avg", "max"] as const).map((m, i) => (
              <button key={m} onClick={() => setAggMode(m)}
                style={{ padding: "5px 12px", fontSize: 12, fontWeight: m === aggMode ? 700 : 400, background: m === aggMode ? "var(--brand-light)" : "transparent", color: m === aggMode ? "var(--brand)" : "var(--text-secondary)", border: "none", cursor: "pointer", borderRight: i === 0 ? "1px solid var(--border)" : "none" }}>
                {m === "avg" ? "Average" : "Max"}
              </button>
            ))}
          </div>
          {/* Geo */}
          <div style={{ display: "flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
            {(["nat", "ut"] as const).map((g, i) => (
              <button key={g} onClick={() => setGeo(g)}
                style={{ padding: "5px 12px", fontSize: 12, fontWeight: g === geo ? 700 : 400, background: g === geo ? "var(--brand-light)" : "transparent", color: g === geo ? "var(--brand)" : "var(--text-secondary)", border: "none", cursor: "pointer", borderRight: i === 0 ? "1px solid var(--border)" : "none" }}>
                {g === "nat" ? "National" : "Utah"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Search + filters ── */}
      <div style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)", padding: "12px 24px 10px", flexShrink: 0 }}>
        {/* Search bar */}
        <div style={{ position: "relative", marginBottom: 8 }}>
          <span style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", display: "flex", alignItems: "center" }}>
            <SearchIcon />
          </span>
          <input
            type="text" placeholder="Search occupations…" value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setSearchFocused(true)} onBlur={() => setSearchFocused(false)}
            style={{
              width: "100%", fontSize: 13,
              border: `1px solid ${searchFocused ? "var(--brand)" : "var(--border)"}`,
              borderRadius: 8, padding: "8px 12px 8px 32px",
              background: "var(--bg-surface)", color: "var(--text-primary)",
              outline: "none", boxSizing: "border-box",
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
        <div style={{ display: "flex", gap: 5, flexWrap: "wrap", maxHeight: 72, overflowY: "auto" }}>
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

        {/* Table-mode controls */}
        {viewMode === "table" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 10 }}>
            <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
              {/* Level */}
              <div>
                <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", marginRight: 8 }}>Level</span>
                <div style={{ display: "inline-flex", border: "1px solid var(--border)", borderRadius: 7, overflow: "hidden" }}>
                  {(["major", "minor", "broad", "occupation"] as TableLevel[]).map((lv, i, arr) => (
                    <button key={lv} onClick={() => setTableLevel(lv)}
                      style={{ padding: "4px 10px", fontSize: 11, fontWeight: lv === tableLevel ? 600 : 400, background: lv === tableLevel ? "var(--brand-light)" : "transparent", color: lv === tableLevel ? "var(--brand)" : "var(--text-secondary)", border: "none", cursor: "pointer", borderRight: i < arr.length - 1 ? "1px solid var(--border)" : "none" }}>
                      {lv.charAt(0).toUpperCase() + lv.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Auto-aug filter */}
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>
                  Auto-aug ≥ {autoAugMin.toFixed(1)}
                </span>
                <input type="range" min={0} max={5} step={0.1} value={autoAugMin}
                  onChange={(e) => setAutoAugMin(Number(e.target.value))}
                  style={{ width: 90, accentColor: "var(--brand)" }} />
                {autoAugMin > 0 && (
                  <button onClick={() => setAutoAugMin(0)}
                    style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>Reset</button>
                )}
              </div>

              {/* Employment filter */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>Min Emp</span>
                <input
                  type="number" min={0} step={1000} value={minEmp || ""}
                  placeholder="0"
                  onChange={(e) => setMinEmp(Number(e.target.value) || 0)}
                  style={{ width: 80, fontSize: 11, border: "1px solid var(--border)", borderRadius: 5, padding: "3px 6px", background: "var(--bg-surface)", color: "var(--text-primary)", outline: "none" }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
                  onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
                />
                {minEmp > 0 && <button onClick={() => setMinEmp(0)} style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>×</button>}
              </div>

              {/* Wage filter */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>Min Wage ($)</span>
                <input
                  type="number" min={0} step={5000} value={minWage || ""}
                  placeholder="0"
                  onChange={(e) => setMinWage(Number(e.target.value) || 0)}
                  style={{ width: 90, fontSize: 11, border: "1px solid var(--border)", borderRadius: 5, padding: "3px 6px", background: "var(--bg-surface)", color: "var(--text-primary)", outline: "none" }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = "var(--brand)")}
                  onBlur={(e)  => (e.currentTarget.style.borderColor = "var(--border)")}
                />
                {minWage > 0 && <button onClick={() => setMinWage(0)} style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>×</button>}
              </div>

              {/* Physical filter (tasks in drilldown) */}
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>Tasks</span>
                <div style={{ display: "inline-flex", border: "1px solid var(--border)", borderRadius: 5, overflow: "hidden" }}>
                  {([
                    { v: "all"     as const, l: "All"       },
                    { v: "exclude" as const, l: "No Phys"   },
                    { v: "only"    as const, l: "Phys only" },
                  ] as const).map(({ v, l }, i, arr) => (
                    <button key={v} onClick={() => setPhysicalMode(v)}
                      style={{ padding: "3px 8px", fontSize: 11, cursor: "pointer", border: "none",
                        borderRight: i < arr.length - 1 ? "1px solid var(--border)" : "none",
                        background: physicalMode === v ? "var(--brand-light)" : "transparent",
                        color: physicalMode === v ? "var(--brand)" : "var(--text-secondary)",
                        fontWeight: physicalMode === v ? 600 : 400,
                      }}>{l}</button>
                  ))}
                </div>
              </div>

              {/* % Tasks Affected filter (shown only when computed) */}
              {pctAffectedMap && (
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>
                    % Affected ≥ {minPctAffected.toFixed(1)}%
                  </span>
                  <input type="range" min={0} max={100} step={0.5} value={minPctAffected}
                    onChange={(e) => setMinPctAffected(Number(e.target.value))}
                    style={{ width: 90, accentColor: "var(--brand)" }} />
                  {minPctAffected > 0 && (
                    <button onClick={() => setMinPctAffected(0)}
                      style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>Reset</button>
                  )}
                </div>
              )}
            </div>

            {/* % Tasks Affected compute panel */}
            <PctComputePanel
              config={config} geo={geo}
              onResult={(map) => { setPctAffectedMap(map); if (!map) setMinPctAffected(0); }}
            />
          </div>
        )}

        {/* Accordion-mode additional controls */}
        {viewMode === "accordion" && (
          <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 10, flexWrap: "wrap" }}>
            {/* Auto-aug threshold */}
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>
                Auto-aug ≥ {autoAugMin.toFixed(1)}
              </span>
              <input type="range" min={0} max={5} step={0.1} value={autoAugMin}
                onChange={(e) => setAutoAugMin(Number(e.target.value))}
                style={{ width: 90, accentColor: "var(--brand)" }} />
              {autoAugMin > 0 && (
                <button onClick={() => setAutoAugMin(0)}
                  style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>Reset</button>
              )}
            </div>
            {/* Physical filter for tasks in accordion */}
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.07em", whiteSpace: "nowrap" }}>Tasks</span>
              <div style={{ display: "inline-flex", border: "1px solid var(--border)", borderRadius: 5, overflow: "hidden" }}>
                {([
                  { v: "all"     as const, l: "All"       },
                  { v: "exclude" as const, l: "No Phys"   },
                  { v: "only"    as const, l: "Phys only" },
                ] as const).map(({ v, l }, i, arr) => (
                  <button key={v} onClick={() => setPhysicalMode(v)}
                    style={{ padding: "3px 8px", fontSize: 11, cursor: "pointer", border: "none",
                      borderRight: i < arr.length - 1 ? "1px solid var(--border)" : "none",
                      background: physicalMode === v ? "var(--brand-light)" : "transparent",
                      color: physicalMode === v ? "var(--brand)" : "var(--text-secondary)",
                      fontWeight: physicalMode === v ? 600 : 400,
                    }}>{l}</button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Content ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 24px" }}>
        {viewMode === "table" ? (
          <FlatTable
            occupations={filtered} geo={geo} aggMode={aggMode}
            tableLevel={tableLevel} autoAugMin={autoAugMin}
            minEmp={minEmp} minWage={minWage}
            pctAffectedMap={pctAffectedMap} minPctAffected={minPctAffected}
            physicalMode={physicalMode}
          />
        ) : filtered.length === 0 ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200, fontSize: 13, color: "var(--text-muted)" }}>
            No occupations match your search.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {majorGroups.map(([mName, mOccs]) => (
              <MajorBlock
                key={mName} name={mName} occs={mOccs} aggMode={aggMode} geo={geo}
                autoOpen={searchActive} physicalMode={physicalMode} autoAugMin={autoAugMin}
              />
            ))}
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
