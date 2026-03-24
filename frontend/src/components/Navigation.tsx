"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSimpleMode } from "@/lib/SimpleModeContext";

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

        {/* Simple / Advanced toggle */}
        <button
          onClick={toggle}
          style={{
            marginLeft: 12,
            display: "flex",
            alignItems: "center",
            gap: 7,
            padding: "5px 12px",
            borderRadius: 7,
            border: "1px solid var(--border)",
            background: isSimple ? "var(--brand-light)" : "transparent",
            cursor: "pointer",
            transition: "all 0.15s",
            flexShrink: 0,
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
        </button>

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
