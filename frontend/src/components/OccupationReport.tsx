"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import type {
  ColorBucket,
  ConfigResponse,
  OccupationReport,
  OccReportTask,
  OccReportWaRow,
  OccReportSkaRow,
  OccReportHierarchyEntry,
} from "@/lib/types";
import {
  fetchOccupationReport,
  fetchOccupationReportTitles,
} from "@/lib/api";

type PickerMode = "search" | "browse";

interface Props {
  config: ConfigResponse;
}

/* ── Neutral 3-tier color palette ─────────────────────────────────────────── */

const BUCKET_BG: Record<ColorBucket, string> = {
  high: "rgba(184, 96, 60, 0.16)",
  mid:  "rgba(214, 165, 96, 0.14)",
  low:  "rgba(110, 138, 156, 0.12)",
  none: "rgba(228, 228, 222, 0.30)",
};
const BUCKET_BORDER: Record<ColorBucket, string> = {
  high: "rgba(184, 96, 60, 0.40)",
  mid:  "rgba(214, 165, 96, 0.40)",
  low:  "rgba(110, 138, 156, 0.40)",
  none: "rgba(155, 155, 155, 0.30)",
};
const BUCKET_DOT: Record<ColorBucket, string> = {
  high: "#b8603c",
  mid:  "#d6a560",
  low:  "#6e8a9c",
  none: "#9b9b9b",
};
const BUCKET_LABEL: Record<ColorBucket, string> = {
  high: "More automated usage seen",
  mid:  "More augmentative",
  low:  "Less automated usage seen",
  none: "No data",
};

const TIER_COLORS: Record<string, { bg: string; fg: string; label: string }> = {
  high:     { bg: "rgba(184, 96, 60, 0.20)",  fg: "#8a4225", label: "High Risk" },
  mod_high: { bg: "rgba(214, 165, 96, 0.22)", fg: "#8b6420", label: "Mod-High Risk" },
  mod_low:  { bg: "rgba(160, 160, 130, 0.20)", fg: "#5f5f4c", label: "Mod-Low Risk" },
  low:      { bg: "rgba(110, 138, 156, 0.18)", fg: "#3e5664", label: "Low Risk" },
};

/* ── Formatters ───────────────────────────────────────────────────────────── */

function fmtNumber(v: number | null | undefined, decimals = 0): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
function fmtAuto(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(2);
}
function fmtWage(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
}
function fmtPctOfNeed(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${v.toFixed(0)}%`;
}
function fmtRank(rank: number | undefined, total: number): string {
  if (rank === undefined) return "—";
  return `#${rank} of ${total}`;
}

/* ── Job zone / outlook interpretations ───────────────────────────────────── */

const JOB_ZONE_INTERP: Record<number, string> = {
  1: "Little to no preparation",
  2: "Some preparation",
  3: "Medium preparation",
  4: "Considerable preparation",
  5: "Extensive preparation",
};

const OUTLOOK_INTERP: Record<number, string> = {
  0: "Limited outlook, low wages",
  1: "Strong outlook, low wages",
  2: "Limited outlook, high wages",
  3: "Moderate outlook, low–mod wages",
  4: "Good outlook, high wages",
  5: "Strongest outlook, high wages",
};

/* ── Component ────────────────────────────────────────────────────────────── */

export default function OccupationReport({ config }: Props) {
  const [titles, setTitles] = useState<string[]>([]);
  const [hierarchy, setHierarchy] = useState<OccReportHierarchyEntry[]>([]);
  const [selectedTitle, setSelectedTitle] = useState<string>("");
  const [pickerMode, setPickerMode] = useState<PickerMode>("search");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const [geo, setGeo] = useState<string>("nat");
  const [report, setReport] = useState<OccupationReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [waLevel, setWaLevel] = useState<"gwa" | "iwa" | "dwa">("gwa");
  const [showRiskFlags, setShowRiskFlags] = useState<boolean>(false);

  // Load titles + hierarchy once
  useEffect(() => {
    fetchOccupationReportTitles()
      .then((d) => {
        setTitles(d.titles);
        setHierarchy(d.hierarchy);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Debounce: don't refetch on every search keystroke; only when title is selected
  const loadReport = useCallback((title: string, g: string) => {
    if (!title) return;
    setLoading(true);
    setError(null);
    fetchOccupationReport(title, g)
      .then((r) => setReport(r))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedTitle) loadReport(selectedTitle, geo);
  }, [selectedTitle, geo, loadReport]);

  const filteredTitles = useMemo(() => {
    if (!searchQuery) return titles.slice(0, 12);
    const q = searchQuery.toLowerCase();
    return titles.filter((t) => t.toLowerCase().includes(q)).slice(0, 12);
  }, [searchQuery, titles]);

  const handleSelect = (t: string) => {
    setSelectedTitle(t);
    setSearchQuery(t);
    setShowSuggestions(false);
  };

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px 80px" }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
          My Occupation Report
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 0, lineHeight: 1.5 }}>
          Pick your occupation and see, in one place, where AI already does the work, where you still
          have an advantage, what tasks to delegate, and how your role compares to similar ones. All numbers
          are drawn from the dashboard&apos;s <strong>all-confirmed (conservative)</strong> dataset:
          measured AI usage across Anthropic Claude conversations, AEI API/agentic tool-use, and Microsoft
          Copilot, with physical Microsoft tasks excluded.
        </p>
      </header>

      <Picker
        pickerMode={pickerMode}
        setPickerMode={setPickerMode}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        showSuggestions={showSuggestions}
        setShowSuggestions={setShowSuggestions}
        filteredTitles={filteredTitles}
        onSelect={handleSelect}
        selectedTitle={selectedTitle}
        hierarchy={hierarchy}
        geo={geo}
        setGeo={setGeo}
        geoOptions={config.geo_options}
      />

      {error && (
        <div style={{
          marginTop: 24, padding: "14px 18px", borderRadius: 8,
          background: "rgba(184, 96, 60, 0.10)", color: "#8a4225",
          border: "1px solid rgba(184, 96, 60, 0.40)",
        }}>
          {error}
        </div>
      )}

      {!selectedTitle && !loading && (
        <div style={{
          marginTop: 32, padding: "48px 24px", borderRadius: 12,
          background: "var(--bg-sidebar)", border: "1px solid var(--border)",
          textAlign: "center", color: "var(--text-secondary)",
        }}>
          <p style={{ fontSize: 15, marginBottom: 8 }}>Search for your occupation above to begin.</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Try: <em>Registered Nurses, Software Developers, Customer Service Representatives, Lawyers, …</em>
          </p>
        </div>
      )}

      {loading && (
        <div style={{ marginTop: 48, textAlign: "center" }}>
          <div style={{
            display: "inline-block", width: 36, height: 36, borderRadius: "50%",
            border: "3px solid var(--brand)", borderTopColor: "transparent",
            animation: "spin 0.7s linear infinite",
          }} />
          <p style={{ marginTop: 12, fontSize: 13, color: "var(--text-muted)" }}>
            Building your report…
          </p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {!loading && report && (
        <ReportBody
          report={report}
          waLevel={waLevel}
          setWaLevel={setWaLevel}
          showRiskFlags={showRiskFlags}
          setShowRiskFlags={setShowRiskFlags}
        />
      )}
    </div>
  );
}

/* ── Picker (Search + Browse tabs) ────────────────────────────────────────── */

interface PickerProps {
  pickerMode: PickerMode;
  setPickerMode: (m: PickerMode) => void;
  searchQuery: string;
  setSearchQuery: (s: string) => void;
  showSuggestions: boolean;
  setShowSuggestions: (b: boolean) => void;
  filteredTitles: string[];
  onSelect: (t: string) => void;
  selectedTitle: string;
  hierarchy: OccReportHierarchyEntry[];
  geo: string;
  setGeo: (g: string) => void;
  geoOptions: Record<string, string>;
}

function Picker(props: PickerProps) {
  const { pickerMode, setPickerMode, geo, setGeo, geoOptions } = props;
  return (
    <div style={{
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 10, padding: 14,
    }}>
      {/* Tab row + geo dropdown */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, gap: 12 }}>
        <div style={{ display: "flex", gap: 4 }}>
          <PickerTab label="Search"
                     active={pickerMode === "search"}
                     onClick={() => setPickerMode("search")} />
          <PickerTab label="Browse by category"
                     active={pickerMode === "browse"}
                     onClick={() => setPickerMode("browse")} />
        </div>
        <select
          value={geo}
          onChange={(e) => setGeo(e.target.value)}
          style={{
            padding: "8px 14px", border: "1px solid var(--border)",
            borderRadius: 8, fontSize: 13, cursor: "pointer",
            background: "var(--bg-surface)", color: "var(--text-primary)",
            minWidth: 180,
          }}
        >
          {Object.entries(geoOptions).map(([code, name]) => (
            <option key={code} value={code}>{name}</option>
          ))}
        </select>
      </div>

      {pickerMode === "search" ? <SearchPanel {...props} /> : <BrowsePanel {...props} />}
    </div>
  );
}

function PickerTab({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "7px 14px", borderRadius: 6,
        fontSize: 13, fontWeight: active ? 600 : 500,
        background: active ? "var(--brand-light)" : "transparent",
        color: active ? "var(--brand)" : "var(--text-secondary)",
        border: "1px solid",
        borderColor: active ? "var(--brand-light)" : "transparent",
        cursor: "pointer",
        transition: "all 0.13s",
      }}
    >
      {label}
    </button>
  );
}

function SearchPanel({
  searchQuery, setSearchQuery, showSuggestions, setShowSuggestions,
  filteredTitles, onSelect,
}: PickerProps) {
  return (
    <div style={{ position: "relative" }}>
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => { setSearchQuery(e.target.value); setShowSuggestions(true); }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        placeholder="Search for your occupation (e.g. Registered Nurses)…"
        style={{
          width: "100%", padding: "10px 14px",
          border: "1px solid var(--border)", borderRadius: 8,
          fontSize: 14, outline: "none",
          transition: "border-color 0.15s",
        }}
      />
      {showSuggestions && filteredTitles.length > 0 && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0, zIndex: 20,
          maxHeight: 320, overflowY: "auto",
          background: "var(--bg-surface)", border: "1px solid var(--border)",
          borderRadius: 8, boxShadow: "0 6px 20px rgba(0,0,0,0.10)",
        }}>
          {filteredTitles.map((t) => (
            <button
              key={t}
              onMouseDown={() => onSelect(t)}
              style={{
                display: "block", width: "100%", textAlign: "left",
                padding: "9px 14px", fontSize: 13,
                background: "transparent", border: "none", cursor: "pointer",
                color: "var(--text-primary)",
                borderBottom: "1px solid var(--border-light)",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-base)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {t}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Browse panel (cascading Major → Minor → Broad → Occupation) ────────── */

function BrowsePanel({ hierarchy, onSelect, selectedTitle }: PickerProps) {
  const [major, setMajor] = useState<string>("");
  const [minor, setMinor] = useState<string>("");
  const [broad, setBroad] = useState<string>("");

  // Distinct sorted lists derived from hierarchy + current selections
  const majors = useMemo(() => {
    const s = new Set<string>();
    hierarchy.forEach((h) => h.major && s.add(h.major));
    return Array.from(s).sort();
  }, [hierarchy]);

  const minors = useMemo(() => {
    if (!major) return [];
    const s = new Set<string>();
    hierarchy.forEach((h) => h.major === major && h.minor && s.add(h.minor));
    return Array.from(s).sort();
  }, [hierarchy, major]);

  const broads = useMemo(() => {
    if (!minor) return [];
    const s = new Set<string>();
    hierarchy.forEach((h) => h.minor === minor && h.broad && s.add(h.broad));
    return Array.from(s).sort();
  }, [hierarchy, minor]);

  const occs = useMemo(() => {
    if (!broad) return [];
    return hierarchy.filter((h) => h.broad === broad).map((h) => h.title).sort();
  }, [hierarchy, broad]);

  // Auto-clear downstream selections when an upstream one changes
  const onMajor = (m: string) => { setMajor(m); setMinor(""); setBroad(""); };
  const onMinor = (m: string) => { setMinor(m); setBroad(""); };

  // If user already selected an occupation via search, prefill the dropdowns
  // so the Browse view reflects "where am I".
  useEffect(() => {
    if (!selectedTitle || !hierarchy.length) return;
    const found = hierarchy.find((h) => h.title === selectedTitle);
    if (!found) return;
    if (found.major && found.major !== major) setMajor(found.major);
    if (found.minor && found.minor !== minor) setMinor(found.minor);
    if (found.broad && found.broad !== broad) setBroad(found.broad);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTitle, hierarchy.length]);

  return (
    <div>
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 10,
      }}>
        <BrowseSelect label="Major"
                      value={major}
                      options={majors}
                      placeholder="Pick a major category…"
                      onChange={onMajor} />
        <BrowseSelect label="Minor"
                      value={minor}
                      options={minors}
                      placeholder={major ? "Pick a minor…" : "Pick a major first"}
                      onChange={onMinor}
                      disabled={!major} />
        <BrowseSelect label="Broad"
                      value={broad}
                      options={broads}
                      placeholder={minor ? "Pick a broad…" : "Pick a minor first"}
                      onChange={setBroad}
                      disabled={!minor} />
      </div>

      {broad ? (
        <div style={{
          maxHeight: 280, overflowY: "auto",
          border: "1px solid var(--border-light)", borderRadius: 8,
          background: "var(--bg-base)",
        }}>
          {occs.length === 0 && (
            <p style={{ padding: 14, fontSize: 13, color: "var(--text-muted)" }}>
              No occupations under this broad category.
            </p>
          )}
          {occs.map((t) => {
            const isSelected = t === selectedTitle;
            return (
              <button
                key={t}
                onClick={() => onSelect(t)}
                style={{
                  display: "block", width: "100%", textAlign: "left",
                  padding: "10px 14px", fontSize: 13,
                  background: isSelected ? "var(--brand-light)" : "transparent",
                  color: isSelected ? "var(--brand)" : "var(--text-primary)",
                  border: "none", cursor: "pointer",
                  borderBottom: "1px solid var(--border-light)",
                  fontWeight: isSelected ? 600 : 400,
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) e.currentTarget.style.background = "var(--bg-surface)";
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) e.currentTarget.style.background = "transparent";
                }}
              >
                {t}
              </button>
            );
          })}
        </div>
      ) : (
        <p style={{ fontSize: 12, color: "var(--text-muted)", padding: "12px 4px 4px" }}>
          Pick a Major → Minor → Broad to see the occupations under that branch.
        </p>
      )}
    </div>
  );
}

function BrowseSelect({
  label, value, options, placeholder, onChange, disabled,
}: {
  label: string;
  value: string;
  options: string[];
  placeholder: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <div>
      <p style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase",
                  letterSpacing: "0.04em", marginBottom: 4 }}>
        {label}
      </p>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%", padding: "9px 12px",
          border: "1px solid var(--border)", borderRadius: 8,
          fontSize: 13, cursor: disabled ? "not-allowed" : "pointer",
          background: disabled ? "var(--bg-base)" : "var(--bg-surface)",
          color: value ? "var(--text-primary)" : "var(--text-muted)",
          opacity: disabled ? 0.6 : 1,
        }}
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (<option key={o} value={o}>{o}</option>))}
      </select>
    </div>
  );
}

/* ── Report body ──────────────────────────────────────────────────────────── */

function ReportBody({
  report, waLevel, setWaLevel, showRiskFlags, setShowRiskFlags,
}: {
  report: OccupationReport;
  waLevel: "gwa" | "iwa" | "dwa";
  setWaLevel: (l: "gwa" | "iwa" | "dwa") => void;
  showRiskFlags: boolean;
  setShowRiskFlags: (b: boolean) => void;
}) {
  return (
    <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 32 }}>
      <Hero report={report} showRiskFlags={showRiskFlags} setShowRiskFlags={setShowRiskFlags} />
      <Headline report={report} />
      <Trend report={report} />
      <GroupRanks report={report} />
      <Sector report={report} />
      <SkaSection report={report} />
      <TasksSection report={report} />
      <WaSection report={report} waLevel={waLevel} setWaLevel={setWaLevel} />
      <TechSection report={report} />
      <SimilarSection report={report} />
      <PaletteFooter />
    </div>
  );
}

/* ── Hero card ────────────────────────────────────────────────────────────── */

function Hero({
  report, showRiskFlags, setShowRiskFlags,
}: { report: OccupationReport; showRiskFlags: boolean; setShowRiskFlags: (b: boolean) => void }) {
  const h = report.headline;
  const tier = h.risk.tier;
  const tierStyle = TIER_COLORS[tier] ?? TIER_COLORS.low;
  const jzInterp = h.job_zone ? JOB_ZONE_INTERP[Math.round(h.job_zone)] : null;
  const olInterp = h.dws_star_rating ? OUTLOOK_INTERP[Math.round(h.dws_star_rating)] : null;
  return (
    <section style={{
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 12, padding: "24px 28px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 24, flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 280 }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
            {h.title}
          </h2>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 14 }}>
            {[h.broad, h.minor, h.major].filter(Boolean).join(" · ")}
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {h.job_zone !== null && h.job_zone !== undefined && (
              <Chip label={`Job Zone ${h.job_zone.toFixed(0)}`} sub={jzInterp ?? ""} />
            )}
            {h.dws_star_rating !== null && h.dws_star_rating !== undefined && (
              <Chip label={`Outlook ${h.dws_star_rating.toFixed(0)}`} sub={olInterp ?? ""} />
            )}
            {h.n_tasks !== null && h.n_tasks !== undefined && (
              <Chip label={`${h.n_tasks} tasks`} sub="O*NET task profile" />
            )}
          </div>
        </div>
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8,
        }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 10,
            padding: "8px 14px", borderRadius: 999,
            background: tierStyle.bg, color: tierStyle.fg,
            fontSize: 13, fontWeight: 600,
          }}>
            <span>{tierStyle.label} · {h.risk.score}/10</span>
          </div>
          <button
            onClick={() => setShowRiskFlags(!showRiskFlags)}
            style={{
              fontSize: 11, padding: "4px 10px", borderRadius: 6,
              background: "transparent", border: "1px solid var(--border)",
              color: "var(--text-muted)", cursor: "pointer",
            }}
          >
            {showRiskFlags ? "Hide" : "Why?"}
          </button>
        </div>
      </div>
      {showRiskFlags && (
        <RiskFlagsTable risk={h.risk} />
      )}
    </section>
  );
}

function Chip({ label, sub }: { label: string; sub: string }) {
  return (
    <div style={{
      padding: "6px 12px", borderRadius: 999,
      background: "var(--brand-light)", color: "var(--brand)",
      fontSize: 12, fontWeight: 500,
    }}>
      <span style={{ fontWeight: 600 }}>{label}</span>
      {sub && <span style={{ marginLeft: 6, fontWeight: 400, color: "var(--text-secondary)" }}>· {sub}</span>}
    </div>
  );
}

const RISK_FLAG_LABELS: Record<string, string> = {
  flag1_pct:        "Pct tasks affected > 50%",
  flag2_ska:        "SKA percentage > median",
  flag3_pct_trend:  "Pct trend rising fast",
  flag4_ska_trend:  "SKA gap rising fast",
  flag5_job_zone:   "Job zone 1–3",
  flag6_outlook:    "Outlook 2–3",
  flag7_n_software: "n_software > median",
  flag8_auto_aug:   "Auto-aug > median",
};

function RiskFlagsTable({ risk }: { risk: OccupationReport["headline"]["risk"] }) {
  return (
    <div style={{
      marginTop: 18, padding: 14, borderRadius: 8,
      background: "var(--bg-base)", border: "1px solid var(--border-light)",
    }}>
      <p style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8, lineHeight: 1.4 }}>
        Risk score is built from 8 binary flags weighted 1× or 2×. High requires a score of 8+ AND
        pct_tasks_affected ≥ 33%; otherwise it caps at Mod-High.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 6 }}>
        {Object.entries(RISK_FLAG_LABELS).map(([key, lbl]) => {
          const v = (risk.flags as unknown as Record<string, number>)[key] ?? 0;
          return (
            <div key={key} style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "5px 10px", borderRadius: 6,
              background: v ? "rgba(184, 96, 60, 0.08)" : "transparent",
              border: "1px solid var(--border-light)",
              fontSize: 12,
            }}>
              <span style={{ color: v ? "var(--text-primary)" : "var(--text-muted)" }}>{lbl}</span>
              <span style={{ fontWeight: 600, color: v ? "#8a4225" : "var(--text-muted)" }}>
                {v ? "✓" : "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Headline numbers ─────────────────────────────────────────────────────── */

function Headline({ report }: { report: OccupationReport }) {
  const h = report.headline;
  return (
    <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
      <Stat label="% Tasks Affected" value={h.pct_tasks_affected !== null && h.pct_tasks_affected !== undefined ? `${h.pct_tasks_affected}%` : "—"} />
      <Stat label="Workers Affected" value={fmtNumber(h.workers_affected)} />
      <Stat label="Wages Affected" value={fmtWage(h.wages_affected)} />
      <Stat label="Total Employment" value={fmtNumber(h.emp)} />
      <Stat label="Median Wage" value={fmtWage(h.wage)} />
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 10, padding: "16px 18px",
    }}>
      <p style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 6 }}>
        {label}
      </p>
      <p style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)" }}>{value}</p>
    </div>
  );
}

/* ── Trend sparkline ──────────────────────────────────────────────────────── */

function Trend({ report }: { report: OccupationReport }) {
  const points = report.trend.filter((p) => p.pct_tasks_affected !== null && p.pct_tasks_affected !== undefined);
  if (points.length < 2) return null;
  const vals = points.map((p) => p.pct_tasks_affected as number);
  const minV = Math.min(...vals, 0);
  const maxV = Math.max(...vals, 1);
  const range = maxV - minV || 1;
  const W = 720, H = 80, pad = 12;
  const pathPoints = points.map((p, i) => {
    const x = pad + (i / (points.length - 1)) * (W - 2 * pad);
    const y = H - pad - (((p.pct_tasks_affected as number) - minV) / range) * (H - 2 * pad);
    return [x, y];
  });
  const path = pathPoints.map(([x, y], i) => (i === 0 ? `M ${x},${y}` : `L ${x},${y}`)).join(" ");
  const first = vals[0]; const last = vals[vals.length - 1];
  const delta = last - first;
  return (
    <section style={{
      background: "var(--bg-surface)", border: "1px solid var(--border)",
      borderRadius: 12, padding: "20px 24px",
    }}>
      <SectionHeading
        title="Exposure trend"
        sub={`% of tasks affected over the past year. ${delta >= 0 ? "+" : ""}${delta.toFixed(1)} pp from ${points[0].date} to ${points[points.length - 1].date}.`}
      />
      <div style={{ display: "flex", alignItems: "center", gap: 18, flexWrap: "wrap", marginTop: 12 }}>
        <svg width="100%" height={H + 30} viewBox={`0 0 ${W} ${H + 30}`} preserveAspectRatio="none" style={{ maxWidth: W }}>
          <path d={path} stroke="var(--brand)" strokeWidth={2.5} fill="none" />
          {pathPoints.map(([x, y], i) => (
            <g key={i}>
              <circle cx={x} cy={y} r={3.5} fill="var(--brand)" />
              <text x={x} y={H + 22} textAnchor="middle" fontSize={10} fill="var(--text-muted)">
                {points[i].date.slice(0, 7)}
              </text>
              <text x={x} y={y - 8} textAnchor="middle" fontSize={10} fill="var(--text-secondary)">
                {(points[i].pct_tasks_affected as number).toFixed(0)}%
              </text>
            </g>
          ))}
        </svg>
      </div>
    </section>
  );
}

/* ── Group rankings ───────────────────────────────────────────────────────── */

function GroupRanks({ report }: { report: OccupationReport }) {
  const r = report.group_ranks;
  const intensity = report.headline.intensity;
  const RankCard = ({ scope, ranks }: { scope: string; ranks?: typeof r.economy | null }) => {
    if (!ranks) return null;
    return (
      <div style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 10, padding: "14px 16px",
      }}>
        <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em",
                    color: "var(--text-muted)", marginBottom: 8 }}>
          {scope} <span style={{ textTransform: "none", color: "var(--text-muted)" }}>(of {ranks.total})</span>
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
          <RankRow label="% Tasks" v={ranks.pct} total={ranks.total} />
          <RankRow label="Workers" v={ranks.workers} total={ranks.total} />
          <RankRow label="Wages"   v={ranks.wages} total={ranks.total} />
        </div>
      </div>
    );
  };
  return (
    <section>
      <SectionHeading
        title="Where you stand"
        sub="Where this occupation ranks within its broader categories on the headline metrics. Lower number = more exposed/affected."
      />
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: 12, marginTop: 12,
      }}>
        <RankCard scope="Economy" ranks={r.economy} />
        <RankCard scope="Major"   ranks={r.major} />
        <RankCard scope="Minor"   ranks={r.minor} />
        <RankCard scope="Broad"   ranks={r.broad} />
        {intensity.occ_intensity_rank !== null && intensity.occ_intensity_rank !== undefined && (
          <div style={{
            background: "var(--bg-surface)", border: "1px solid var(--border)",
            borderRadius: 10, padding: "14px 16px",
          }}>
            <p style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em",
                        color: "var(--text-muted)", marginBottom: 8 }}>
              Intensity ranks <span style={{ textTransform: "none" }}>(per-task usage)</span>
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-secondary)" }}>Occupation</span>
                <span style={{ fontWeight: 600 }}>
                  {fmtRank(intensity.occ_intensity_rank ?? undefined, intensity.occ_intensity_total ?? 0)}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "var(--text-secondary)" }}>Major</span>
                <span style={{ fontWeight: 600 }}>
                  {fmtRank(intensity.major_intensity_rank ?? undefined, intensity.major_intensity_total ?? 0)}
                </span>
              </div>
            </div>
            <p style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 8, lineHeight: 1.4 }}>
              Per-capacity AI usage (Σ pct ÷ Σ freq×emp), bias-corrected for source asymmetries.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

function RankRow({ label, v, total }: { label: string; v?: number; total: number }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between" }}>
      <span style={{ color: "var(--text-secondary)" }}>{label}</span>
      <span style={{ fontWeight: 600 }}>{fmtRank(v, total)}</span>
    </div>
  );
}

/* ── Sector at a glance ───────────────────────────────────────────────────── */

function Sector({ report }: { report: OccupationReport }) {
  const s = report.sector;
  if (!s.major) return null;
  return (
    <section>
      <SectionHeading title="Your sector at a glance" sub={s.major} />
      <div style={{
        background: "var(--bg-surface)", border: "1px solid var(--border)",
        borderRadius: 12, padding: "20px 24px", marginTop: 12,
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16,
      }}>
        <SectorStat label="% Tasks Affected" value={`${(s.pct_tasks_affected ?? 0).toFixed(1)}%`}
                    rank={s.rank_pct} total={s.n_majors} />
        <SectorStat label="Workers Affected" value={fmtNumber(s.workers_affected)}
                    rank={s.rank_workers} total={s.n_majors} />
        <SectorStat label="Wages Affected"   value={fmtWage(s.wages_affected)}
                    rank={s.rank_wages} total={s.n_majors} />
      </div>
    </section>
  );
}

function SectorStat({ label, value, rank, total }: { label: string; value: string; rank?: number; total?: number }) {
  return (
    <div>
      <p style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase",
                  letterSpacing: "0.04em", marginBottom: 6 }}>
        {label}
      </p>
      <p style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)" }}>{value}</p>
      {rank !== undefined && total !== undefined && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
          {fmtRank(rank, total)} sectors
        </p>
      )}
    </div>
  );
}

/* ── SKA section ──────────────────────────────────────────────────────────── */

function SkaSection({ report }: { report: OccupationReport }) {
  const s = report.ska.summary;
  return (
    <section>
      <SectionHeading
        title="Where you lead, where AI leads"
        sub="Skills + Knowledge + Abilities (importance ≥ 3 only). “AI capability” is the top-10-occupation average for that element. Above 100% of need = AI leads. Sorted with biggest AI lead at top."
      />
      <div style={{
        marginTop: 12, padding: "14px 18px", background: "var(--bg-surface)",
        border: "1px solid var(--border)", borderRadius: 10,
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12,
      }}>
        <SkaSummaryStat label="Overall" pct={s.overall_pct} />
        <SkaSummaryStat label="Skills" pct={s.skills_pct} />
        <SkaSummaryStat label="Abilities" pct={s.abilities_pct} />
        <SkaSummaryStat label="Knowledge" pct={s.knowledge_pct} />
      </div>

      <SkaTable title="Skills" rows={report.ska.rows.skills} />
      <SkaTable title="Knowledge" rows={report.ska.rows.knowledge} />
      <SkaTable title="Abilities" rows={report.ska.rows.abilities} />
    </section>
  );
}

function SkaSummaryStat({ label, pct }: { label: string; pct?: number | null }) {
  if (pct === null || pct === undefined) return null;
  const bucket: ColorBucket = pct >= 100 ? "high" : pct >= 66 ? "mid" : "low";
  return (
    <div>
      <p style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase",
                  letterSpacing: "0.04em", marginBottom: 4 }}>
        {label}
      </p>
      <p style={{ fontSize: 18, fontWeight: 700, color: BUCKET_DOT[bucket] }}>
        {pct.toFixed(0)}%
      </p>
      <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
        AI capability vs. occ requirement
      </p>
    </div>
  );
}

function SkaTable({ title, rows }: { title: string; rows: OccReportSkaRow[] }) {
  if (!rows.length) return null;
  return (
    <div style={{ marginTop: 18 }}>
      <h4 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>
        {title}
      </h4>
      <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 10 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--bg-base)", textAlign: "left" }}>
              <Th>Element</Th>
              <Th align="right">Importance</Th>
              <Th align="right">Level</Th>
              <Th align="right">Your score</Th>
              <Th align="right">AI top-10</Th>
              <Th align="right">AI as % of need</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} style={{
                background: BUCKET_BG[r.color_bucket],
                borderTop: "1px solid var(--border-light)",
              }}>
                <Td>
                  <span style={{
                    display: "inline-block", width: 8, height: 8, borderRadius: "50%",
                    background: BUCKET_DOT[r.color_bucket], marginRight: 8,
                  }} />
                  {r.element}
                </Td>
                <Td align="right">{fmtNumber(r.importance, 1)}</Td>
                <Td align="right">{fmtNumber(r.level, 1)}</Td>
                <Td align="right">{fmtNumber(r.occ_score, 1)}</Td>
                <Td align="right">{fmtNumber(r.ai_top10, 1)}</Td>
                <Td align="right" style={{ fontWeight: 600 }}>{fmtPctOfNeed(r.pct_of_need)}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tasks ────────────────────────────────────────────────────────────────── */

function TasksSection({ report }: { report: OccupationReport }) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const toggle = (key: string) => {
    const next = new Set(expanded);
    next.has(key) ? next.delete(key) : next.add(key);
    setExpanded(next);
  };
  return (
    <section>
      <SectionHeading
        title="Tasks AI can help with"
        sub={
          <>
            Each task is rated by all four data sources (AEI Conv = Claude conversational, AEI API = agentic
            tool-use, Microsoft Copilot, MCP servers). The colored bar reflects the max across AEI Conv, AEI API,
            and Microsoft. <strong>AEI API</strong> specifically captures agentic AI capability: where it&apos;s
            high, the work can be done by AI tools acting on its own (file edits, API calls, browsing) rather
            than just chat. Click a task to see the top MCP servers that match it.
          </>
        }
      />
      <PaletteLegend />
      <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 10, marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--bg-base)", textAlign: "left" }}>
              <Th>#</Th>
              <Th>Task</Th>
              <Th align="right">Importance</Th>
              <Th align="right">AEI Conv (max)</Th>
              <Th align="right">AEI API (max)</Th>
              <Th align="right">Microsoft</Th>
              <Th align="right">MCP</Th>
              <Th></Th>
            </tr>
          </thead>
          <tbody>
            {report.tasks.map((t) => {
              const isOpen = expanded.has(t.task_normalized);
              return (
                <TaskRow key={t.task_normalized} t={t} isOpen={isOpen} onToggle={() => toggle(t.task_normalized)} />
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function TaskRow({ t, isOpen, onToggle }: { t: OccReportTask; isOpen: boolean; onToggle: () => void }) {
  return (
    <>
      <tr
        onClick={onToggle}
        style={{
          background: BUCKET_BG[t.color_bucket],
          borderTop: "1px solid var(--border-light)",
          cursor: t.top_mcps.length ? "pointer" : "default",
        }}
      >
        <Td>{t.rank}</Td>
        <Td>
          <span style={{
            display: "inline-block", width: 8, height: 8, borderRadius: "50%",
            background: BUCKET_DOT[t.color_bucket], marginRight: 8, flexShrink: 0,
          }} />
          {t.task}
        </Td>
        <Td align="right">{fmtNumber(t.importance, 1)}</Td>
        <Td align="right">{fmtAuto(t.aei_conv_max)}</Td>
        <Td align="right">{fmtAuto(t.aei_api_max)}</Td>
        <Td align="right">{fmtAuto(t.microsoft)}</Td>
        <Td align="right">{fmtAuto(t.mcp)}</Td>
        <Td>
          {t.top_mcps.length > 0 && (
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{isOpen ? "▼" : "▶"}</span>
          )}
        </Td>
      </tr>
      {isOpen && t.top_mcps.length > 0 && (
        <tr style={{ background: "var(--bg-base)" }}>
          <td colSpan={8} style={{ padding: "12px 18px", borderTop: "1px solid var(--border-light)" }}>
            <p style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase",
                        letterSpacing: "0.04em", marginBottom: 8 }}>
              Top MCP servers
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {t.top_mcps.map((m, i) => (
                <div key={i} style={{
                  padding: "8px 12px", background: "var(--bg-surface)",
                  border: "1px solid var(--border)", borderRadius: 8, fontSize: 12,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                      {m.url ? <a href={m.url} target="_blank" rel="noreferrer" style={{ color: "var(--brand)" }}>{m.title}</a> : m.title}
                    </span>
                    {m.rating !== null && m.rating !== undefined && (
                      <span style={{ color: "var(--text-muted)" }}>rating {m.rating}</span>
                    )}
                  </div>
                  {m.description && (
                    <p style={{ color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      {m.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

/* ── Work activities section ─────────────────────────────────────────────── */

function WaSection({
  report, waLevel, setWaLevel,
}: { report: OccupationReport; waLevel: "gwa" | "iwa" | "dwa"; setWaLevel: (l: "gwa" | "iwa" | "dwa") => void }) {
  const rows = report.work_activities[waLevel];
  return (
    <section>
      <SectionHeading
        title="Your work activities"
        sub="The same per-source AI ratings, rolled up to the categories your tasks fall into. Useful when you want a higher-level view than individual tasks."
      />
      <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
        {(["gwa", "iwa", "dwa"] as const).map((lvl) => (
          <button
            key={lvl}
            onClick={() => setWaLevel(lvl)}
            style={{
              padding: "6px 14px", borderRadius: 6, fontSize: 12, fontWeight: 600,
              cursor: "pointer", border: "1px solid var(--border)",
              background: waLevel === lvl ? "var(--brand-light)" : "var(--bg-surface)",
              color: waLevel === lvl ? "var(--brand)" : "var(--text-secondary)",
            }}
          >
            {lvl.toUpperCase()}
          </button>
        ))}
      </div>
      <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 10, marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--bg-base)", textAlign: "left" }}>
              <Th>#</Th>
              <Th>{waLevel.toUpperCase()}</Th>
              <Th align="right"># Tasks</Th>
              <Th align="right">AEI Conv avg</Th>
              <Th align="right">AEI API avg</Th>
              <Th align="right">Microsoft avg</Th>
              <Th align="right">MCP avg</Th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (<WaRow key={r.name} r={r} />))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function WaRow({ r }: { r: OccReportWaRow }) {
  return (
    <tr style={{ background: BUCKET_BG[r.color_bucket], borderTop: "1px solid var(--border-light)" }}>
      <Td>{r.rank}</Td>
      <Td>
        <span style={{
          display: "inline-block", width: 8, height: 8, borderRadius: "50%",
          background: BUCKET_DOT[r.color_bucket], marginRight: 8,
        }} />
        {r.name}
      </Td>
      <Td align="right">{r.n_tasks}</Td>
      <Td align="right">{fmtAuto(r.aei_conv_max)}</Td>
      <Td align="right">{fmtAuto(r.aei_api_max)}</Td>
      <Td align="right">{fmtAuto(r.microsoft)}</Td>
      <Td align="right">{fmtAuto(r.mcp)}</Td>
    </tr>
  );
}

/* ── Tech tools ───────────────────────────────────────────────────────────── */

function TechSection({ report }: { report: OccupationReport }) {
  if (!report.tech.length) return null;
  // Show top 25 by commodity rank (most-exposed first)
  const visible = report.tech.slice(0, 25);
  return (
    <section>
      <SectionHeading
        title="Software tools your job uses"
        sub="From the O*NET technology skills inventory for this occupation. Commodity rank = where this software category ranks among all categories on average AI exposure (lower = more AI leverage in that category economy-wide)."
      />
      <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 10, marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--bg-base)", textAlign: "left" }}>
              <Th>Software</Th>
              <Th>Commodity</Th>
              <Th align="right">Commodity rank</Th>
              <Th align="right">Avg % tasks affected</Th>
            </tr>
          </thead>
          <tbody>
            {visible.map((t, i) => (
              <tr key={i} style={{ borderTop: "1px solid var(--border-light)" }}>
                <Td>{t.software}</Td>
                <Td>{t.commodity}</Td>
                <Td align="right">{t.commodity_rank ? `#${t.commodity_rank} of ${t.commodity_total}` : "—"}</Td>
                <Td align="right">{t.commodity_avg_pct !== null && t.commodity_avg_pct !== undefined ? `${t.commodity_avg_pct.toFixed(1)}%` : "—"}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {report.tech.length > 25 && (
        <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
          Showing top 25 of {report.tech.length} software entries (sorted by commodity rank).
        </p>
      )}
    </section>
  );
}

/* ── Similar occupations ──────────────────────────────────────────────────── */

function SimilarSection({ report }: { report: OccupationReport }) {
  if (!report.similar.length) return null;
  return (
    <section>
      <SectionHeading
        title="Similar occupations"
        sub="Closest match by Skills + Knowledge + Abilities profile (L1 distance over importance×level vectors). Useful for seeing whether occupations with similar skill demands face similar AI exposure."
      />
      <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: 10, marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--bg-base)", textAlign: "left" }}>
              <Th>Occupation</Th>
              <Th>Sector</Th>
              <Th align="right">% Tasks Affected</Th>
              <Th align="right">Median Wage</Th>
              <Th align="right">Job Zone</Th>
              <Th align="right">Outlook</Th>
              <Th align="right">SKA distance</Th>
            </tr>
          </thead>
          <tbody>
            {report.similar.map((o, i) => (
              <tr key={i} style={{ borderTop: "1px solid var(--border-light)" }}>
                <Td>{o.title}</Td>
                <Td style={{ color: "var(--text-secondary)", fontSize: 12 }}>{o.major}</Td>
                <Td align="right">{o.pct_tasks_affected !== null && o.pct_tasks_affected !== undefined ? `${o.pct_tasks_affected}%` : "—"}</Td>
                <Td align="right">{fmtWage(o.wage)}</Td>
                <Td align="right">{o.job_zone ?? "—"}</Td>
                <Td align="right">{o.dws_star_rating ?? "—"}</Td>
                <Td align="right" style={{ color: "var(--text-muted)" }}>{fmtNumber(o.distance, 1)}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/* ── Palette legend ───────────────────────────────────────────────────────── */

function PaletteLegend() {
  return (
    <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap", marginTop: 8 }}>
      {(["high", "mid", "low"] as ColorBucket[]).map((b) => (
        <div key={b} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--text-secondary)" }}>
          <span style={{
            display: "inline-block", width: 12, height: 12, borderRadius: 3,
            background: BUCKET_BG[b], border: `1px solid ${BUCKET_BORDER[b]}`,
          }} />
          {BUCKET_LABEL[b]}
        </div>
      ))}
    </div>
  );
}

function PaletteFooter() {
  return (
    <p style={{ fontSize: 11, color: "var(--text-muted)", textAlign: "center", marginTop: 12, lineHeight: 1.5 }}>
      Colors are tied to demonstrated AI usage levels: tasks with higher max auto-aug scores (≥4 across AEI
      Conv, AEI API, and Microsoft) show as &ldquo;more automated usage seen&rdquo;; 2.5–4 as &ldquo;more
      augmentative&rdquo;; below 2.5 as &ldquo;less automated usage seen.&rdquo; SKA elements use the same
      three-tier framing on AI capability as a percentage of the occupation&apos;s requirement (≥100% / 66–100% /
      &lt;66%). Source: <strong>{`AEI Both + Micro Conservative 2026-02-12`}</strong> for headline metrics
      and SKA; per-source auto-aug from the explorer task lookup.
    </p>
  );
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */

function SectionHeading({ title, sub }: { title: string; sub: React.ReactNode }) {
  return (
    <div>
      <h3 style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
        {title}
      </h3>
      <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>{sub}</p>
    </div>
  );
}

function Th({ children, align = "left" }: { children?: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th style={{
      padding: "10px 14px", fontSize: 11, fontWeight: 600,
      color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em",
      textAlign: align,
    }}>
      {children}
    </th>
  );
}

function Td({
  children, align = "left", style,
}: { children?: React.ReactNode; align?: "left" | "right"; style?: React.CSSProperties }) {
  return (
    <td style={{
      padding: "10px 14px", color: "var(--text-primary)",
      textAlign: align, verticalAlign: "top",
      ...(style ?? {}),
    }}>
      {children}
    </td>
  );
}
