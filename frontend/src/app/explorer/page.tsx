"use client";

import { useEffect, useState } from "react";
import type { OccupationSummary, ConfigResponse } from "@/lib/types";
import { fetchExplorerOccupations, fetchConfig } from "@/lib/api";
import ExplorerView from "@/components/ExplorerView";

export default function ExplorerPage() {
  const [occs,   setOccs]   = useState<OccupationSummary[] | null>(null);
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [error,  setError]  = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchExplorerOccupations(), fetchConfig()])
      .then(([o, c]) => { setOccs(o); setConfig(c); })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)" }}>
      <p style={{ color: "#b91c1c" }}>Backend error: {error}</p>
    </div>
  );

  if (!occs || !config) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)", gap: 16 }}>
      <div style={{ width: 36, height: 36, borderRadius: "50%", border: "3px solid var(--brand)", borderTopColor: "transparent", animation: "spin 0.7s linear infinite" }} />
      <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading occupation data…</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  return <ExplorerView occupations={occs} config={config} />;
}
