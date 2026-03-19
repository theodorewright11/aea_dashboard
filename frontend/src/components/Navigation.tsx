"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/explorer",        label: "Occupation Explorer" },
  { href: "/wa-explorer",     label: "WA Explorer" },
  { href: "/",                label: "Occupation Categories" },
  { href: "/work-activities", label: "Work Activities" },
  { href: "/trends",          label: "Trends" },
  { href: "/instructions",    label: "Instructions" },
  { href: "/about",           label: "About" },
];

/* ── Navigation ──────────────────────────────────────────────────── */

export default function Navigation() {
  const pathname = usePathname();

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
        <div style={{ marginLeft: 12, display: "flex", alignItems: "center", flexShrink: 0 }}>
          <span style={{ fontSize: 11, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
            AEI · O*NET · BLS OEWS
          </span>
        </div>
      </nav>
    </>
  );
}
