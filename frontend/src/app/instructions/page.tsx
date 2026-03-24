"use client";

import { useState } from "react";

/* ── Shared styles ───────────────────────────────────────────────── */

const headStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.08em",
  marginBottom: 8,
  marginTop: 0,
};

const bodyStyle: React.CSSProperties = {
  fontSize: 14,
  color: "var(--text-secondary)",
  lineHeight: 1.7,
  margin: "0 0 10px",
};

const liStyle: React.CSSProperties = {
  fontSize: 14,
  color: "var(--text-secondary)",
  lineHeight: 1.65,
  marginBottom: 6,
};

const codeStyle: React.CSSProperties = {
  fontSize: 12,
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  padding: "1px 5px",
  borderRadius: 3,
  fontFamily: "monospace",
};

const formulaBoxStyle: React.CSSProperties = {
  margin: "10px 0 14px",
  padding: "12px 16px",
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  borderRadius: 8,
  fontSize: 13,
  fontFamily: "monospace",
  color: "var(--text-secondary)",
  letterSpacing: "0.01em",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 32 }}>
      <p style={headStyle}>{title}</p>
      {children}
    </div>
  );
}

function SubHead({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", margin: "16px 0 6px" }}>
      {children}
    </p>
  );
}

/* ── Interactive Calculator ──────────────────────────────────────── */

function Calculator() {
  const [freqMean, setFreqMean] = useState(4.5);
  const [importance, setImportance] = useState(3.0);
  const [relevance, setRelevance] = useState(60);
  const [autoAug, setAutoAug] = useState(2.5);
  const [method, setMethod] = useState<"freq" | "imp">("freq");

  const taskComp = method === "freq"
    ? freqMean * (autoAug / 5)
    : (relevance * Math.pow(2, importance)) * (autoAug / 5);

  const taskCompBase = method === "freq"
    ? freqMean
    : relevance * Math.pow(2, importance);

  const augMultiplier = autoAug / 5;
  const fmt = (v: number, d = 3) => v.toFixed(d);

  const sliderStyle: React.CSSProperties = {
    width: "100%", accentColor: "var(--brand)", cursor: "pointer",
  };

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderRadius: 10,
      padding: "20px 24px",
      marginTop: 10,
    }}>
      {/* Method toggle */}
      <div style={{ display: "flex", gap: 6, marginBottom: 20 }}>
        {(["freq", "imp"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMethod(m)}
            style={{
              padding: "4px 14px",
              borderRadius: 5,
              border: "1px solid",
              borderColor: method === m ? "var(--brand)" : "var(--border)",
              background: method === m ? "var(--brand-light)" : "transparent",
              color: method === m ? "var(--brand)" : "var(--text-secondary)",
              fontWeight: method === m ? 600 : 400,
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            {m === "freq" ? "Frequency" : "Importance-weighted"}
          </button>
        ))}
      </div>

      {/* Sliders */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px 28px" }}>
        {method === "freq" && (
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              freq_mean: <strong style={{ color: "var(--text-primary)" }}>{fmt(freqMean, 1)}</strong>
              <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> (0–10)</span>
            </span>
            <input type="range" min={0} max={10} step={0.1} value={freqMean}
              onChange={(e) => setFreqMean(+e.target.value)} style={sliderStyle} />
          </label>
        )}
        {method === "imp" && (
          <>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                importance: <strong style={{ color: "var(--text-primary)" }}>{fmt(importance, 1)}</strong>
                <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> (0–5)</span>
              </span>
              <input type="range" min={0} max={5} step={0.1} value={importance}
                onChange={(e) => setImportance(+e.target.value)} style={sliderStyle} />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                relevance: <strong style={{ color: "var(--text-primary)" }}>{fmt(relevance, 0)}</strong>
                <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> (0–100)</span>
              </span>
              <input type="range" min={0} max={100} step={1} value={relevance}
                onChange={(e) => setRelevance(+e.target.value)} style={sliderStyle} />
            </label>
          </>
        )}
        <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            auto_aug_mean: <strong style={{ color: "var(--text-primary)" }}>{fmt(autoAug, 1)}</strong>
            <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> (0–5)</span>
          </span>
          <input type="range" min={0} max={5} step={0.1} value={autoAug}
            onChange={(e) => setAutoAug(+e.target.value)} style={sliderStyle} />
        </label>
      </div>

      {/* Result */}
      <div style={{
        marginTop: 20,
        padding: "14px 18px",
        background: "var(--bg-base)",
        borderRadius: 8,
        border: "1px solid var(--border-light)",
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}>
        <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 2 }}>Step-by-step result</div>
        {method === "freq" ? (
          <div style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "monospace" }}>
            <div>base = freq_mean = <strong style={{ color: "var(--text-primary)" }}>{fmt(freqMean, 2)}</strong></div>
            <div>multiplier = auto_aug / 5 = {fmt(autoAug, 1)} / 5 = <strong style={{ color: "var(--text-primary)" }}>{fmt(augMultiplier, 3)}</strong></div>
          </div>
        ) : (
          <div style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "monospace" }}>
            <div>base = relevance × 2^importance = {fmt(relevance, 0)} × 2^{fmt(importance, 1)} = <strong style={{ color: "var(--text-primary)" }}>{fmt(taskCompBase, 2)}</strong></div>
            <div>multiplier = auto_aug / 5 = {fmt(autoAug, 1)} / 5 = <strong style={{ color: "var(--text-primary)" }}>{fmt(augMultiplier, 3)}</strong></div>
          </div>
        )}
        <div style={{
          marginTop: 6,
          paddingTop: 10,
          borderTop: "1px solid var(--border-light)",
          fontSize: 14,
          fontWeight: 600,
          color: "var(--brand)",
          fontFamily: "monospace",
        }}>
          task_comp = {fmt(taskCompBase, 2)} × {fmt(augMultiplier, 3)} = {fmt(taskComp, 4)}
        </div>
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────── */

export default function InstructionsPage() {
  return (
    <div style={{
      minHeight: "calc(100vh - var(--nav-height))",
      background: "var(--bg-base)",
      padding: "40px 24px 80px",
      display: "flex",
      justifyContent: "center",
    }}>
      <div style={{ maxWidth: 760, width: "100%" }}>

        {/* Header */}
        <div style={{ marginBottom: 36 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 6px", letterSpacing: "-0.02em" }}>
            Instructions & Methodology
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)", margin: 0 }}>
            How to use each page, how metrics are computed, and what the data represents.
          </p>
        </div>

        {/* ── Page Guides ─────────────────────────── */}
        <Section title="Page Guide">

          <SubHead>Occupation Categories</SubHead>
          <p style={bodyStyle}>
            Compare two groups of occupations side-by-side. Each group is independently
            configured with its own dataset selection, aggregation level, and filters.
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}><strong>Datasets</strong> — select one or more AI scoring datasets. When multiple are selected, choose <em>Average</em> or <em>Max</em> to combine scores.</li>
            <li style={liStyle}><strong>Aggregation</strong> — roll up results to Major Category, Minor Category, Broad Occupation, or individual Occupation.</li>
            <li style={liStyle}><strong>Geography</strong> — National or Utah employment/wage figures from BLS OEWS 2024.</li>
            <li style={liStyle}><strong>Method</strong> — Frequency or Importance-weighted task completion (see Metrics section below).</li>
            <li style={liStyle}><strong>Physical filter</strong> — excludes tasks flagged as truly physical; useful for isolating cognitive/informational tasks.</li>
            <li style={liStyle}><strong>Auto-aug multiplier</strong> — when On, scales task weight by the AI automatability score (0–5 scale, divided by 5).</li>
            <li style={liStyle}><strong>Top N / Search</strong> — show the top N categories by the selected sort metric, or search for a specific category with ±context window.</li>
          </ul>

          <SubHead>Work Activities</SubHead>
          <p style={bodyStyle}>
            Same layout as Occupation Categories, but aggregated over O*NET work activities
            (GWA → IWA → DWA hierarchy) instead of occupation groups.
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}><strong>Activity level</strong> — GWA (17 groups), IWA (~300 groups), or DWA (~2,000 items).</li>
            <li style={liStyle}>AEI datasets use the O*NET 2015 task baseline; MCP / Microsoft use the 2025 baseline. Mixing families across groups is not supported.</li>
          </ul>

          <SubHead>Trends</SubHead>
          <p style={bodyStyle}>
            Time-series view showing how automation exposure has changed across dataset
            snapshot dates for each series (AEI, MCP, Microsoft).
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}><strong>Dataset pills</strong> — select individual versions (e.g. AEI v2) to include. The backend fetches the full family; the frontend filters to selected versions.</li>
            <li style={liStyle}><strong>Line mode</strong> — <em>Individual</em> draws one line per (dataset × category); <em>Average</em> averages across selected datasets at each date; <em>Max</em> shows the cumulative running max (never decreases).</li>
            <li style={liStyle}><strong>Freeze tooltip</strong> — click a data point to freeze a scrollable tooltip panel near it; click again or elsewhere to unfreeze.</li>
          </ul>

          <SubHead>Occupation Explorer</SubHead>
          <p style={bodyStyle}>
            Flat sortable table across all 923 occupations, pre-computed across all 8 AI
            scoring sources. Drill into any row to see individual tasks and per-source scores.
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}><strong>Level selector</strong> — Major / Minor / Broad / Occupation / Task. Task level shows one row per unique O*NET task.</li>
            <li style={liStyle}><strong>Column filters</strong> — click the filter icon on any column header to add a ≥ / ≤ threshold filter.</li>
            <li style={liStyle}><strong>Auto-aug min slider</strong> — filters rows to those where the average or max AI score is at or above the threshold.</li>
            <li style={liStyle}><strong>Pct Compute</strong> — optional panel to run the full computation pipeline and overlay % tasks affected directly in the table.</li>
          </ul>

          <SubHead>Work Activities Explorer</SubHead>
          <p style={bodyStyle}>
            Same explorer layout for the work activity hierarchy (GWA → IWA → DWA).
            Expand any DWA row to see the tasks assigned to that activity and their AI scores.
          </p>

        </Section>

        {/* ── Metrics ─────────────────────────── */}
        <Section title="Metrics & Formulas">

          <SubHead>Task Completion Weight</SubHead>
          <p style={bodyStyle}>
            Every O*NET task has survey-measured frequency, importance, and relevance.
            The task completion weight (task_comp) captures how much a task contributes
            to an occupation&apos;s total work.
          </p>
          <div style={formulaBoxStyle}>
            Frequency method:  task_comp = freq_mean<br />
            Importance method: task_comp = relevance × 2^importance
          </div>
          <p style={bodyStyle}>
            When the Auto-aug multiplier is On, both methods scale by the AI automatability
            score:
          </p>
          <div style={formulaBoxStyle}>
            task_comp (with auto-aug) = task_comp × (auto_aug_mean / 5)
          </div>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            MCP datasets use <code style={codeStyle}>auto_aug_mean_adj</code> (adjusted score
            excluding low-confidence ratings) instead of <code style={codeStyle}>auto_aug_mean</code>.
          </p>

          <SubHead>% Tasks Affected</SubHead>
          <p style={bodyStyle}>
            The share of total task completion weight that is attributable to AI-automatable
            tasks, relative to the ECO baseline across all O*NET tasks for that occupation.
          </p>
          <div style={formulaBoxStyle}>
            % Tasks Affected = Σ(AI task_comp) / Σ(ECO task_comp) × 100
          </div>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            This is always a ratio-of-totals, never an average of per-task percentages.
            The ECO denominator covers all tasks; the AI numerator covers only tasks present
            in the AI dataset.
          </p>

          <SubHead>Workers & Wages Affected</SubHead>
          <div style={formulaBoxStyle}>
            Workers affected = (% Tasks Affected / 100) × Employment<br />
            Wages affected   = (% Tasks Affected / 100) × Employment × Median Annual Wage
          </div>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            Employment and median annual wage come from BLS OEWS 2024, national or Utah.
          </p>

          <SubHead>Explorer Metrics (Auto Avg / Auto Max)</SubHead>
          <p style={bodyStyle}>
            For each task, up to 8 sources provide an AI automatability score. The explorer
            shows two variants:
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}><strong>Avg↑ / Max↑ (with values)</strong> — averaged only over tasks that have at least one non-null source score.</li>
            <li style={liStyle}><strong>Avg (all) / Max (all)</strong> — same, but null scores are treated as zero; covers all tasks in the group.</li>
            <li style={liStyle}><strong>Σ Pct Avg / Σ Pct Max</strong> — sum (not average) of per-task conversation share (pct_normalized) across tasks with values.</li>
          </ul>

        </Section>

        {/* ── Interactive Calculator ─────────────────────────── */}
        <Section title="Interactive Calculator">
          <p style={bodyStyle}>
            Adjust the sliders to see how task_comp is computed for a single task.
          </p>
          <Calculator />
        </Section>

        {/* ── SOC Structure ─────────────────────────── */}
        <Section title="Occupation Categories (SOC Structure)">
          <p style={bodyStyle}>
            Occupations are organized using the U.S. Standard Occupational Classification
            (SOC) 2018 system, with four levels of hierarchy:
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}><strong>Major group</strong> — 23 broad categories (e.g. &quot;Management Occupations&quot;, &quot;Healthcare Practitioners&quot;). Two-digit SOC code.</li>
            <li style={liStyle}><strong>Minor group</strong> — ~100 groups within major categories. Four-digit SOC code (e.g. &quot;Top Executives&quot;).</li>
            <li style={liStyle}><strong>Broad occupation</strong> — ~450 groups. Six-digit SOC code ending in 0 (e.g. &quot;General and Operations Managers&quot;).</li>
            <li style={liStyle}><strong>Detailed occupation</strong> — ~923 specific job titles in this dataset. Six-digit SOC code (e.g. &quot;Chief Executives&quot;).</li>
          </ul>
          <p style={bodyStyle}>
            AEI datasets use 2010 SOC codes; they are mapped to 2019 SOC via the O*NET
            crosswalk before comparison with MCP and Microsoft datasets.
          </p>
        </Section>

        {/* ── Work Activities ─────────────────────────── */}
        <Section title="O*NET Work Activities (GWA / IWA / DWA)">
          <p style={bodyStyle}>
            O*NET organizes work activities into a three-level hierarchy:
          </p>
          <ul style={{ margin: "0 0 14px", paddingLeft: 22 }}>
            <li style={liStyle}>
              <strong>GWA — Generalized Work Activities</strong> (17 categories) — broadest grouping,
              e.g. &quot;Getting Information&quot;, &quot;Communicating with Supervisors&quot;, &quot;Processing Information&quot;.
            </li>
            <li style={liStyle}>
              <strong>IWA — Intermediate Work Activities</strong> (~300 items) — mid-level,
              e.g. &quot;Collect data or information&quot;, &quot;Coordinate with others to resolve problems&quot;.
            </li>
            <li style={liStyle}>
              <strong>DWA — Detailed Work Activities</strong> (~2,000 items) — most granular,
              directly associated with individual O*NET tasks.
            </li>
          </ul>
          <p style={bodyStyle}>
            A single task can map to multiple DWAs. In the Work Activities analysis, each
            DWA receives the full employment allocation of the task — they are independent
            activity dimensions, not subdivisions of a single task.
          </p>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            AEI datasets use O*NET 2015 DWA associations; MCP and Microsoft use O*NET 2025.
          </p>
        </Section>

        {/* ── Dataset Dates ─────────────────────────── */}
        <Section title="Dataset Snapshot Dates">
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", fontSize: 13, width: "100%" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "6px 16px 6px 0", color: "var(--text-primary)", fontWeight: 600 }}>Dataset</th>
                  <th style={{ textAlign: "left", padding: "6px 16px 6px 0", color: "var(--text-primary)", fontWeight: 600 }}>Version</th>
                  <th style={{ textAlign: "left", padding: "6px 0", color: "var(--text-primary)", fontWeight: 600 }}>Date</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["AEI", "v1", "Dec 23, 2024"],
                  ["AEI", "v2", "Mar 6, 2025"],
                  ["AEI", "v3", "Aug 11, 2025"],
                  ["AEI", "v4", "Nov 13, 2025"],
                  ["AEI API", "v3", "Aug 11, 2025"],
                  ["AEI API", "v4", "Nov 13, 2025"],
                  ["MCP", "v1", "Apr 24, 2025"],
                  ["MCP", "v2", "May 24, 2025"],
                  ["MCP", "v3", "Jul 23, 2025"],
                  ["MCP", "v4", "Feb 18, 2026"],
                  ["Microsoft", "—", "Sep 30, 2024"],
                ].map(([src, ver, date], i) => (
                  <tr key={i} style={{ borderBottom: "1px solid var(--border-light)" }}>
                    <td style={{ padding: "6px 16px 6px 0", color: "var(--text-secondary)" }}>{src}</td>
                    <td style={{ padding: "6px 16px 6px 0", color: "var(--text-secondary)" }}>{ver}</td>
                    <td style={{ padding: "6px 0", color: "var(--text-muted)", fontFamily: "monospace", fontSize: 12 }}>{date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

      </div>
    </div>
  );
}
