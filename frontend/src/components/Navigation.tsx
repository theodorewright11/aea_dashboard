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
                  <div style={{ marginBottom: 4 }}><strong>Fixed settings:</strong> All datasets, Time method, All physical tasks, Auto-aug On (adjusted).</div>
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

        {/* Right side — spacer for alignment */}
        <div style={{ marginLeft: 12, flexShrink: 0 }} />
      </nav>
    </>
  );
}
