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

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <p style={sectionHeadStyle}>{title}</p>
      {children}
    </div>
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
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 6px", letterSpacing: "-0.02em" }}>
            About This Dashboard
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            Automation Exposure Analysis · AEI Project
          </p>
        </div>

        {/* Overview */}
        <p style={{ ...bodyStyle, marginBottom: 28 }}>
          Built for Utah&apos;s{" "}
          <strong style={{ color: "var(--text-primary)", fontWeight: 600 }}>
            Office of Artificial Intelligence Policy (OAIP)
          </strong>{" "}
          as part of the{" "}
          <strong style={{ color: "var(--text-primary)", fontWeight: 600 }}>
            Anthropic Economic Index (AEI)
          </strong>{" "}
          project. Visualizes AI automation exposure across U.S. occupations, work
          activities, and time using multiple independent AI scoring datasets.
        </p>

        {/* Methodology */}
        <Section title="Methodology">
          <p style={bodyStyle}>
            Automation exposure is measured as the share of weighted task completion
            attributable to AI-automatable tasks, relative to the O*NET ECO baseline:
          </p>
          <div style={{
            margin: "10px 0 14px",
            padding: "12px 16px",
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 13,
            fontFamily: "monospace",
            color: "var(--text-secondary)",
            letterSpacing: "0.01em",
          }}>
            % Tasks Affected = Σ(AI task weight) / Σ(ECO task weight) × 100
          </div>
          <p style={bodyStyle}>Task weights are computed using one of two methods:</p>
          <ul style={{ margin: "6px 0 12px", paddingLeft: 22 }}>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Time</strong> — proportional to
              reported task frequency (
              <code style={{ fontSize: 12, background: "var(--bg-surface)", border: "1px solid var(--border)", padding: "1px 5px", borderRadius: 3 }}>
                freq_mean
              </code>
              )
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Value</strong> — proportional
              to{" "}
              <code style={{ fontSize: 12, background: "var(--bg-surface)", border: "1px solid var(--border)", padding: "1px 5px", borderRadius: 3 }}>
                freq_mean × relevance × importance
              </code>
            </li>
          </ul>
          <p style={bodyStyle}>
            Workers and wages affected are derived by applying % tasks affected to BLS
            OEWS employment and median wage figures respectively.
          </p>
        </Section>

        {/* Data Sources */}
        <Section title="Data Sources">
          <ul style={{ margin: 0, paddingLeft: 22 }}>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>O*NET 2025 / 2015</strong> — Task
              inventory, work activity hierarchy (GWA / IWA / DWA), frequency and
              importance ratings
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>BLS OEWS 2024</strong> — Employment and
              median annual wage by occupation, national and Utah
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Anthropic Economic Index (AEI)</strong> —
              AI automatability scores derived from Claude conversation analysis across
              four snapshot dates (Dec 2024 – Nov 2025)
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>MCP Server Pipeline</strong> — AI task
              classification via Model Context Protocol server logs, four snapshot dates
              (Apr 2025 – Feb 2026)
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Microsoft Occupational AI Analysis</strong> —
              Independent AI exposure ratings across occupations (Sep 2024)
            </li>
          </ul>
        </Section>

        {/* Technical Notes */}
        <Section title="Technical Notes">
          <ul style={{ margin: 0, paddingLeft: 22 }}>
            <li style={liStyle}>
              AEI datasets use 2010 SOC codes and are mapped to 2019 SOC via the O*NET
              crosswalk before comparison with other datasets.
            </li>
            <li style={liStyle}>
              Work Activities analysis uses the O*NET 2015 task baseline for AEI datasets
              and the 2025 baseline for MCP / Microsoft datasets.
            </li>
          </ul>
        </Section>

      </div>
    </div>
  );
}
