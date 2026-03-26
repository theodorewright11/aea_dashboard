"use client";

const sectionHeadStyle: React.CSSProperties = {
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
  marginBottom: 8,
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
  lineHeight: 1.8,
};

const codeStyle: React.CSSProperties = {
  fontSize: 12,
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  padding: "1px 5px",
  borderRadius: 3,
  fontFamily: "monospace",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <p style={sectionHeadStyle}>{title}</p>
      {children}
    </div>
  );
}

function SubHead({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", margin: "14px 0 6px" }}>
      {children}
    </p>
  );
}

export default function AboutPage() {
  return (
    <div style={{
      minHeight: "calc(100vh - var(--nav-height))",
      background: "var(--bg-base)",
      padding: "40px 24px 60px",
      display: "flex",
      justifyContent: "center",
    }}>
      <div style={{ maxWidth: 680, width: "100%" }}>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 6px", letterSpacing: "-0.02em" }}>
            About This Dashboard
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            Automation Exposure Analysis
          </p>
        </div>

        {/* AI disclaimer */}
        <div style={{
          background: "#fffbeb",
          border: "1px solid #f59e0b",
          borderRadius: 8,
          padding: "10px 16px",
          marginBottom: 24,
          fontSize: 12,
          lineHeight: 1.6,
          color: "#92400e",
        }}>
          <strong>Note:</strong> This page was generated with AI and has not been reviewed thoroughly.
          For deeper technical detail, visit the{" "}
          <a href="https://github.com/theodorewright11/aea_dashboard" target="_blank" rel="noopener noreferrer"
            style={{ color: "#d97706", fontWeight: 600 }}>Dashboard GitHub</a>{" "}
          and review the <strong>ARCHITECTURE.md</strong> and <strong>PRD.md</strong> files.
          You can use AI to help summarize any questions you may have.
        </div>

        {/* Overview */}
        <p style={{ ...bodyStyle, marginBottom: 24 }}>
          Built for Utah&apos;s{" "}
          <strong style={{ color: "var(--text-primary)", fontWeight: 600 }}>
            Office of Artificial Intelligence Policy (OAIP)
          </strong>{" "}
          as part of research to explore how AI is impacting the economy.
          Visualizes AI automation exposure across U.S. occupations, work
          activities, and time using multiple independent AI scoring datasets.
        </p>

        {/* How Numbers Are Calculated */}
        <Section title="How Numbers Are Calculated">

          <SubHead>Task Completion Weight (task_comp)</SubHead>
          <p style={bodyStyle}>
            Every O*NET task has survey-measured frequency, importance, and relevance.
            The task completion weight determines how much a task contributes to an occupation&apos;s total work:
          </p>
          <div style={formulaBoxStyle}>
            <strong>Time method:</strong><br />
            task_comp = freq_mean<br /><br />
            <strong>Value method:</strong><br />
            task_comp = freq_mean &times; relevance &times; importance
          </div>

          <SubHead>Auto-Aug Multiplier</SubHead>
          <p style={bodyStyle}>
            When enabled, each task&apos;s weight is scaled by its AI automatability score
            (<code style={codeStyle}>auto_aug_mean</code>, 0&ndash;5 scale):
          </p>
          <div style={formulaBoxStyle}>
            task_comp (with auto-aug) = task_comp &times; (auto_aug_mean / 5)
          </div>

          <SubHead>% Tasks Affected</SubHead>
          <p style={bodyStyle}>
            The share of total weighted task completion attributable to AI-exposed tasks,
            relative to the full ECO baseline for that occupation:
          </p>
          <div style={formulaBoxStyle}>
            % Tasks Affected = &Sigma;(AI task_comp) / &Sigma;(ECO task_comp) &times; 100
          </div>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            Always a ratio-of-totals, never an average of per-task percentages.
            The ECO denominator covers all tasks; the AI numerator covers only tasks present
            in the selected AI dataset(s).
          </p>

          <SubHead>Workers Affected</SubHead>
          <div style={formulaBoxStyle}>
            Workers Affected = (% Tasks Affected / 100) &times; Employment
          </div>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            Employment figures from BLS OEWS 2024 (national or Utah).
          </p>

          <SubHead>Wages Affected</SubHead>
          <div style={formulaBoxStyle}>
            Wages Affected = (% Tasks Affected / 100) &times; Employment &times; Median Annual Wage
          </div>
          <p style={{ ...bodyStyle, fontSize: 12, color: "var(--text-muted)" }}>
            Displayed with adaptive units: $B when &ge; $1B, $M when &ge; $1M, $K when &ge; $1K.
          </p>

          <SubHead>Multi-Dataset Combination</SubHead>
          <p style={bodyStyle}>
            When multiple AI datasets are selected, scores are combined per-task before aggregation:
          </p>
          <div style={formulaBoxStyle}>
            <strong>Average:</strong> combined_score = mean(score across selected datasets)<br />
            <strong>Max:</strong> combined_score = max(score across selected datasets)
          </div>

          <SubHead>Explorer Metrics</SubHead>
          <p style={bodyStyle}>
            Pre-computed across 8 AI sources (AEI v1&ndash;v4, AEI API v3&ndash;v4, MCP v4, Microsoft).
            For each task, up to 8 sources contribute:
          </p>
          <div style={formulaBoxStyle}>
            <strong>Auto Avg&uarr; / Auto Max&uarr;</strong> (with values):<br />
            avg or max of per-task auto_aug scores, only over tasks with &ge; 1 source value<br /><br />
            <strong>Auto Avg (all) / Auto Max (all):</strong><br />
            same, but null scores treated as 0; covers all tasks in the group<br /><br />
            <strong>Pct Avg&uarr; / Pct Max&uarr;:</strong><br />
            avg or max of per-task pct_normalized (share of AI conversations); only tasks with values<br /><br />
            <strong>&Sigma; Pct Avg / &Sigma; Pct Max:</strong><br />
            sum (not average) of per-task pct_normalized across tasks with values
          </div>

          <SubHead>Group-Level Aggregation</SubHead>
          <p style={bodyStyle}>
            At group levels (Major / Minor / Broad), explorer metrics are computed from the
            unique task norms pooled across all occupations in the group &mdash; not averaged
            from per-occupation values. Employment and wages are summed across occupations.
          </p>

          <SubHead>Work Activity Employment Allocation</SubHead>
          <div style={formulaBoxStyle}>
            <strong>Time (freq) weighting:</strong><br />
            emp_allocated = emp &times; (task freq_mean / &Sigma; freq_mean for occ)<br /><br />
            <strong>Value (imp) weighting:</strong><br />
            emp_allocated = emp &times; (task freq&times;rel&times;imp / &Sigma; freq&times;rel&times;imp for occ)
          </div>

        </Section>

        {/* Data Sources */}
        <Section title="Data Sources">
          <ul style={{ margin: 0, paddingLeft: 22 }}>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>O*NET 2025 / 2015</strong> &mdash; Task
              inventory, work activity hierarchy (GWA / IWA / DWA), frequency and
              importance ratings
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>BLS OEWS 2024</strong> &mdash; Employment and
              median annual wage by occupation, national and Utah
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Anthropic Economic Index (AEI)</strong> &mdash;
              AI automatability scores from Claude conversation analysis across
              four snapshot dates (Dec 2024 &ndash; Nov 2025), plus cumulative versions
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>MCP Server Pipeline</strong> &mdash; AI task
              classification via Model Context Protocol server logs, four snapshot dates
              (Apr 2025 &ndash; Feb 2026)
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Microsoft Occupational AI Analysis</strong> &mdash;
              Independent AI exposure ratings across occupations (Sep 2024)
            </li>
          </ul>
        </Section>

      </div>
    </div>
  );
}
