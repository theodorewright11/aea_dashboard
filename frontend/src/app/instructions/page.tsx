"use client";

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
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 6px", letterSpacing: "-0.02em" }}>
            Instructions
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)", margin: 0 }}>
            Quick guide to each page and what you can do with it.
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

        {/* ── Page Guides ─────────────────────────── */}
        <Section title="Pages">

          <SubHead>Occupation Categories</SubHead>
          <p style={bodyStyle}>
            Side-by-side comparison of two groups of occupations. Each group has independent
            dataset selection, aggregation level (Major / Minor / Broad / Occupation), geography,
            and filters. Charts show Workers Affected, Wages Affected, and % Tasks Affected.
            Use Search to find a specific category and Sort to rank by any metric.
          </p>

          <SubHead>Work Activities</SubHead>
          <p style={bodyStyle}>
            Same comparison layout, but organized by O*NET work activity hierarchy
            (GWA / IWA / DWA) instead of occupations. AEI and MCP/Microsoft datasets
            cannot be mixed in the same group because they use different task baselines.
          </p>

          <SubHead>Trends</SubHead>
          <p style={bodyStyle}>
            Time-series line charts showing how exposure metrics change across dataset
            snapshot dates. Select individual dataset versions to include, choose between
            Individual, Average, or Max line modes, and click data points to freeze
            a scrollable tooltip.
          </p>

          <SubHead>Occupation Explorer</SubHead>
          <p style={bodyStyle}>
            Sortable table of all 923 occupations with pre-computed AI exposure metrics.
            Switch between levels (Major / Minor / Broad / Occupation / Task), filter
            columns by thresholds, expand any row to drill into individual tasks and
            per-source scores. The Pct Compute panel lets you run custom computations.
          </p>

          <SubHead>Work Activities Explorer</SubHead>
          <p style={bodyStyle}>
            Same explorer table organized by work activity hierarchy (GWA / IWA / DWA / Task).
            Expand any activity to see its associated tasks and AI scores.
          </p>

          <SubHead>Task Changes Explorer</SubHead>
          <p style={bodyStyle}>
            Compare two dataset versions to see which tasks were added, removed, or had
            score changes. Use status pills to toggle visibility, filter by major category
            or column thresholds, and expand rows for source breakdown details.
          </p>

        </Section>

      </div>
    </div>
  );
}
