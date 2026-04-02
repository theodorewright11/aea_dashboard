"use client";

import { useEffect, useState } from "react";
import type { ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import WAExplorerView from "@/components/WAExplorerView";

export default function WAExplorerPage() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [error,  setError]  = useState<string | null>(null);

  useEffect(() => {
    fetchConfig()
      .then((c) => setConfig(c))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
      <p style={{ color: "#b91c1c" }}>Backend error: {error}</p>
    </div>
  );

  if (!config) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)", gap: 16 }}>
      <div style={{ width: 36, height: 36, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
      <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading work activity data…</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  return <WAExplorerView config={config} />;
}
