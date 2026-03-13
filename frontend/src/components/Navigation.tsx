"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/",                 label: "Overview" },
  { href: "/work-activities",  label: "Work Activities" },
  { href: "/trends",           label: "Trends" },
  { href: "/explorer",         label: "Job Explorer" },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "var(--nav-height)",
        zIndex: 50,
        backgroundColor: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: 0,
        padding: "0 24px",
      }}
    >
      {/* Brand */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginRight: 36 }}>
        <span
          style={{
            fontSize: 15,
            fontWeight: 700,
            color: "var(--brand)",
            letterSpacing: "-0.02em",
            whiteSpace: "nowrap",
          }}
        >
          Automation Exposure
        </span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "var(--text-muted)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          Dashboard
        </span>
      </div>

      {/* Nav links */}
      <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
        {NAV_LINKS.map(({ href, label }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                fontSize: 13,
                fontWeight: active ? 600 : 400,
                color: active ? "var(--brand)" : "var(--text-secondary)",
                backgroundColor: active ? "var(--brand-light)" : "transparent",
                textDecoration: "none",
                transition: "all 0.13s",
                whiteSpace: "nowrap",
              }}
            >
              {label}
            </Link>
          );
        })}
      </div>

      {/* Right side attribution */}
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
          AEI · O*NET · BLS OEWS
        </span>
      </div>
    </nav>
  );
}
