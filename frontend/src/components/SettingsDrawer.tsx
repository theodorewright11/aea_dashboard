"use client";

import { useEffect, useState } from "react";
import type { GroupSettings, ConfigResponse } from "@/lib/types";
import GroupSettingsPanel from "./GroupSettings";
import { GROUP_A_COLOR, GROUP_B_COLOR } from "@/lib/theme";

interface Props {
  open: boolean;
  onClose: () => void;
  onRun: () => void;
  pendingA: GroupSettings;
  pendingB: GroupSettings;
  onChangeA: (s: GroupSettings) => void;
  onChangeB: (s: GroupSettings) => void;
  config: ConfigResponse;
}

export default function SettingsDrawer({
  open, onClose, onRun,
  pendingA, pendingB, onChangeA, onChangeB,
  config,
}: Props) {
  const [activeTab, setActiveTab] = useState<"A" | "B">("A");

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        aria-hidden="true"
        style={{
          position: "fixed", inset: 0, zIndex: 100,
          background: "rgba(0,0,0,0.22)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "all" : "none",
          transition: "opacity 0.2s ease",
        }}
      />

      {/* Drawer panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Dashboard settings"
        style={{
          position: "fixed",
          top: 0, left: 0, bottom: 0,
          zIndex: 101,
          width: "var(--drawer-width)",
          background: "var(--bg-sidebar)",
          borderRight: "1px solid var(--border)",
          display: "flex",
          flexDirection: "column",
          transform: open ? "translateX(0)" : "translateX(-100%)",
          transition: "transform 0.2s ease",
          boxShadow: open ? "6px 0 28px rgba(0,0,0,0.10)" : "none",
        }}
      >
        {/* Header */}
        <div style={{
          padding: "16px 16px 0",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
            Settings
          </span>
          <button
            onClick={onClose}
            aria-label="Close settings"
            style={{
              background: "none", border: "none", cursor: "pointer",
              color: "var(--text-muted)", fontSize: 22, lineHeight: 1,
              padding: "2px 4px", borderRadius: 4,
              transition: "color 0.12s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseOut={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          >
            ×
          </button>
        </div>

        {/* Group A / B tabs */}
        <div style={{
          display: "flex",
          flexShrink: 0,
          marginTop: 14,
          borderBottom: "1px solid var(--border)",
        }}>
          {(["A", "B"] as const).map((tab) => {
            const isActive = activeTab === tab;
            const tabColor = tab === "A" ? GROUP_A_COLOR : GROUP_B_COLOR;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  flex: 1,
                  padding: "9px 0",
                  fontSize: 12,
                  fontWeight: isActive ? 700 : 400,
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  borderBottom: `2px solid ${isActive ? tabColor : "transparent"}`,
                  color: isActive ? tabColor : "var(--text-secondary)",
                  transition: "all 0.12s",
                  letterSpacing: "0.01em",
                }}
              >
                Group {tab}
              </button>
            );
          })}
        </div>

        {/* Settings content — scrollable */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 0" }}>
          {activeTab === "A" ? (
            <GroupSettingsPanel
              groupId="A"
              color={GROUP_A_COLOR}
              settings={pendingA}
              config={config}
              onChange={onChangeA}
            />
          ) : (
            <GroupSettingsPanel
              groupId="B"
              color={GROUP_B_COLOR}
              settings={pendingB}
              config={config}
              onChange={onChangeB}
            />
          )}
        </div>

        {/* Sticky Run button */}
        <div style={{
          flexShrink: 0,
          padding: "12px 16px",
          background: "var(--bg-sidebar)",
          borderTop: "1px solid var(--border)",
        }}>
          <button
            className="btn-brand"
            style={{ width: "100%", padding: "10px 0" }}
            onClick={() => { onRun(); onClose(); }}
          >
            Run
          </button>
        </div>
      </div>
    </>
  );
}
