"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/",                label: "Occupation Categories" },
  { href: "/work-activities", label: "Work Activities" },
  { href: "/trends",          label: "Trends" },
  { href: "/explorer",        label: "Occupation Explorer" },
  { href: "/wa-explorer",     label: "Work Activities Explorer" },
];

/* ── About modal ─────────────────────────────────────────────────── */

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
  fontSize: 13,
  color: "var(--text-secondary)",
  lineHeight: 1.7,
  margin: "0 0 8px",
};

const liStyle: React.CSSProperties = {
  fontSize: 13,
  color: "var(--text-secondary)",
  lineHeight: 1.65,
  marginBottom: 6,
};

function AboutSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 22 }}>
      <p style={sectionHeadStyle}>{title}</p>
      {children}
    </div>
  );
}

function AboutModal({ onClose }: { onClose: () => void }) {
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0, zIndex: 200,
          background: "rgba(0,0,0,0.3)",
        }}
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="About this dashboard"
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 201,
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "28px 32px",
          maxWidth: 560,
          width: "calc(100vw - 48px)",
          maxHeight: "calc(100vh - 80px)",
          overflowY: "auto",
          boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)", margin: "0 0 3px" }}>
              About This Dashboard
            </h2>
            <p style={{ fontSize: 12, color: "var(--text-muted)", margin: 0 }}>
              Automation Exposure Analysis · AEI Project
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: "var(--text-muted)", fontSize: 22, lineHeight: 1,
              padding: "0 0 0 16px", flexShrink: 0,
              transition: "color 0.12s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseOut={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            ×
          </button>
        </div>

        {/* Overview */}
        <p style={{ ...bodyStyle, marginBottom: 20 }}>
          Built for Utah's{" "}
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
        <AboutSection title="Methodology">
          <p style={bodyStyle}>
            Automation exposure is measured as the share of weighted task completion
            attributable to AI-automatable tasks, relative to the O*NET ECO baseline:
          </p>
          <div style={{
            margin: "10px 0 12px",
            padding: "10px 14px",
            background: "var(--bg-base)",
            border: "1px solid var(--border)",
            borderRadius: 7,
            fontSize: 12,
            fontFamily: "monospace",
            color: "var(--text-secondary)",
            letterSpacing: "0.01em",
          }}>
            % Tasks Affected = Σ(AI task weight) / Σ(ECO task weight) × 100
          </div>
          <p style={bodyStyle}>Task weights are computed using one of two methods:</p>
          <ul style={{ margin: "6px 0 10px", paddingLeft: 20 }}>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Frequency</strong> — proportional to
              reported task frequency (<code style={{ fontSize: 11, background: "var(--bg-base)", padding: "1px 4px", borderRadius: 3 }}>freq_mean</code>)
            </li>
            <li style={liStyle}>
              <strong style={{ fontWeight: 600 }}>Importance-weighted</strong> — proportional
              to <code style={{ fontSize: 11, background: "var(--bg-base)", padding: "1px 4px", borderRadius: 3 }}>relevance × 2<sup>importance</sup></code>
            </li>
          </ul>
          <p style={bodyStyle}>
            Workers and wages affected are derived by applying % tasks affected to BLS
            OEWS employment and median wage figures respectively.
          </p>
        </AboutSection>

        {/* Data Sources */}
        <AboutSection title="Data Sources">
          <ul style={{ margin: 0, paddingLeft: 20 }}>
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
        </AboutSection>

        {/* Technical notes */}
        <AboutSection title="Technical Notes">
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li style={liStyle}>
              AEI datasets use 2010 SOC codes and are mapped to 2019 SOC via the O*NET
              crosswalk before comparison with other datasets.
            </li>
            <li style={liStyle}>
              Work Activities analysis uses the O*NET 2015 task baseline for AEI datasets
              and the 2025 baseline for MCP / Microsoft datasets.
            </li>
            <li style={liStyle}>
              MCP datasets include an adjusted auto-aug score (
              <code style={{ fontSize: 11, background: "var(--bg-base)", padding: "1px 4px", borderRadius: 3 }}>auto_aug_mean_adj</code>
              ) that excludes flagged or low-confidence ratings; this is the recommended
              setting for MCP analysis.
            </li>
          </ul>
        </AboutSection>
      </div>
    </>
  );
}

/* ── Navigation ──────────────────────────────────────────────────── */

export default function Navigation() {
  const pathname = usePathname();
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <>
      <nav
        style={{
          position: "fixed",
          top: 0, left: 0, right: 0,
          height: "var(--nav-height)",
          zIndex: 50,
          backgroundColor: "var(--bg-surface)",
          borderTop: "3px solid var(--brand)",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          gap: 0,
        }}
      >
        {/* Brand */}
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", marginRight: 28, flexShrink: 0 }}>
          <span style={{
            fontSize: 14, fontWeight: 600,
            color: "var(--text-primary)",
            letterSpacing: "-0.02em", lineHeight: 1.25,
          }}>
            Automation Exposure
          </span>
          <span style={{
            fontSize: 10, fontWeight: 500,
            color: "var(--text-muted)",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            lineHeight: 1.3,
          }}>
            Analysis Dashboard
          </span>
        </div>

        {/* Nav links — overflow-x scroll on narrow screens */}
        <div style={{
          display: "flex", alignItems: "center", gap: 2,
          overflowX: "auto", flex: 1,
          /* hide scrollbar but keep scrollability */
          scrollbarWidth: "none",
          msOverflowStyle: "none",
        }}>
          {NAV_LINKS.map(({ href, label }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                style={{
                  padding: "6px 13px",
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? "var(--brand)" : "var(--text-secondary)",
                  backgroundColor: active ? "var(--brand-light)" : "transparent",
                  textDecoration: "none",
                  transition: "all 0.13s",
                  whiteSpace: "nowrap",
                  flexShrink: 0,
                }}
              >
                {label}
              </Link>
            );
          })}
        </div>

        {/* Right side */}
        <div style={{ marginLeft: 12, display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
          <span style={{ fontSize: 11, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
            AEI · O*NET · BLS OEWS
          </span>
          <button
            onClick={() => setAboutOpen(true)}
            style={{
              fontSize: 12, fontWeight: 500,
              color: "var(--text-secondary)",
              background: "none",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: "4px 10px",
              cursor: "pointer",
              transition: "all 0.12s",
              whiteSpace: "nowrap",
            }}
            onMouseOver={(e) => { e.currentTarget.style.borderColor = "var(--brand)"; e.currentTarget.style.color = "var(--brand)"; }}
            onMouseOut={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.color = "var(--text-secondary)"; }}
          >
            About
          </button>
        </div>
      </nav>

      {aboutOpen && <AboutModal onClose={() => setAboutOpen(false)} />}
    </>
  );
}
