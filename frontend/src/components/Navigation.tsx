"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSimpleMode } from "@/lib/SimpleModeContext";
import { useState, useRef, useEffect } from "react";

const NAV_LINKS = [
  { href: "/explorer",               label: "Occupation Explorer" },
  { href: "/wa-explorer",            label: "Work Activities Explorer" },
  { href: "/occupation-categories",  label: "Occupation Categories" },
  { href: "/work-activities",        label: "Work Activities" },
  { href: "/trends",                 label: "Trends" },
  { href: "/instructions",           label: "Instructions" },
  { href: "/about",                  label: "About" },
];

/* ── Navigation ──────────────────────────────────────────────────── */

export default function Navigation() {
  const pathname = usePathname();
  const { isSimple, toggle } = useSimpleMode();
  const [showModeTooltip, setShowModeTooltip] = useState(false);

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
            const active = pathname === href || (href !== "/" && pathname.startsWith(href));
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

        {/* Simple / Advanced toggle with tooltip */}
        <div style={{ position: "relative", marginLeft: 12, flexShrink: 0 }}>
          <button
            onClick={toggle}
            onMouseEnter={() => setShowModeTooltip(true)}
            onMouseLeave={() => setShowModeTooltip(false)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              padding: "5px 12px",
              borderRadius: 7,
              border: "1px solid var(--border)",
              background: isSimple ? "var(--brand-light)" : "transparent",
              cursor: "pointer",
              transition: "all 0.15s",
            }}
          >
            <span style={{
              fontSize: 11,
              fontWeight: 600,
              color: isSimple ? "var(--brand)" : "var(--text-secondary)",
              whiteSpace: "nowrap",
            }}>
              {isSimple ? "Simple" : "Advanced"}
            </span>
            {/* Toggle track */}
            <span style={{
              display: "inline-block",
              width: 28,
              height: 16,
              borderRadius: 8,
              backgroundColor: isSimple ? "var(--brand)" : "#ccc",
              position: "relative",
              transition: "background-color 0.15s",
            }}>
              <span style={{
                position: "absolute",
                top: 2,
                left: isSimple ? 14 : 2,
                width: 12,
                height: 12,
                borderRadius: "50%",
                backgroundColor: "#fff",
                transition: "left 0.15s",
                boxShadow: "0 1px 3px rgba(0,0,0,0.15)",
              }} />
            </span>
            {/* Question mark icon */}
            <span style={{
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              width: 14, height: 14, borderRadius: "50%",
              border: "1px solid var(--text-muted)", fontSize: 9, fontWeight: 700,
              color: "var(--text-muted)", lineHeight: 1,
            }}>?</span>
          </button>

          {/* Mode tooltip */}
          {showModeTooltip && (
            <div style={{
              position: "absolute", top: "calc(100% + 6px)", right: 0,
              width: 320, padding: "10px 14px",
              background: "var(--bg-surface)", border: "1px solid var(--border)",
              borderRadius: 8, boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
              zIndex: 100, fontSize: 11, lineHeight: 1.5,
              color: "var(--text-secondary)",
            }}>
              <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>
                {isSimple ? "Simple Mode" : "Advanced Mode"}
              </div>
              {isSimple ? (
                <div>
                  <div style={{ marginBottom: 4 }}><strong>Fixed settings:</strong> All datasets, Frequency method, All physical tasks, Auto-aug On (adjusted).</div>
                  <div style={{ marginBottom: 4 }}><strong>Explorers:</strong> Auto-computes % Tasks Affected. Limited column set.</div>
                  <div style={{ marginBottom: 4 }}><strong>Charts:</strong> Single group (A only). Dataset/Method/Physical/Auto-aug controls hidden.</div>
                  <div><strong>Trends:</strong> Avg/Max lines only. Dataset selection hidden.</div>
                </div>
              ) : (
                <div>
                  <div style={{ marginBottom: 4 }}><strong>Full control:</strong> All datasets, methods, physical filters, auto-aug, and MCP adjusted mean toggles available.</div>
                  <div style={{ marginBottom: 4 }}><strong>Explorers:</strong> Manual % compute via panel. All columns available.</div>
                  <div style={{ marginBottom: 4 }}><strong>Charts:</strong> Two-group (A/B) comparison with independent configs.</div>
                  <div><strong>Trends:</strong> Individual/Avg/Max line modes. Full dataset pill selection.</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right side — source attribution + links */}
        <div style={{ marginLeft: 12, display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          <span style={{ fontSize: 10, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
            Source: 2025 O*NET · 2024 BLS OEWS · Anthropic Economic Index · Microsoft Copilot · MCP Server Classification
          </span>
          <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <a href="https://github.com/theodorewright11/aea_dashboard" target="_blank" rel="noopener noreferrer"
              title="Dashboard GitHub" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 10 }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
            </a>
            <a href="https://github.com/theodorewright11/mcp_to_onet_classification" target="_blank" rel="noopener noreferrer"
              title="MCP Classification GitHub" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 10 }}>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
            </a>
            <a href="mailto:theodorewrightwork@gmail.com" title="Contact" style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: 10 }}>
              <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
            </a>
          </span>
        </div>
      </nav>
    </>
  );
}
