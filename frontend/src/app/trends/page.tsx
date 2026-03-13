"use client";

import { useEffect, useState } from "react";
import type { ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import TrendsView from "@/components/TrendsView";

export default function TrendsPage() {
  const [config, setConfig]           = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig().then(setConfig).catch((e) => setConfigError(e.message));
  }, []);

  if (configError) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
      <p style={{ color: "#b91c1c" }}>Backend error: {configError}</p>
    </div>
  );
  if (!config) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
      <div style={{ width: 32, height: 32, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  return <TrendsView config={config} />;
}
