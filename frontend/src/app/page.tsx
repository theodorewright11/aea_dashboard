"use client";

import { useEffect, useState } from "react";
import type { GroupSettings as GroupSettingsType, ConfigResponse } from "@/lib/types";
import { fetchConfig } from "@/lib/api";
import GroupSettings from "@/components/GroupSettings";
import GroupPanel from "@/components/GroupPanel";

const DEFAULT_A: GroupSettingsType = {
  selectedDatasets: ["AEI v4"],
  combineMethod: "Average",
  method: "freq",
  useAutoAug: false,
  useAdjMean: false,
  physicalMode: "all",
  geo: "nat",
  aggLevel: "major",
  sortBy: "Workers Affected",
  topN: 10,
};

const DEFAULT_B: GroupSettingsType = {
  selectedDatasets: ["MCP v4"],
  combineMethod: "Average",
  method: "freq",
  useAutoAug: false,
  useAdjMean: false,
  physicalMode: "all",
  geo: "nat",
  aggLevel: "major",
  sortBy: "Workers Affected",
  topN: 10,
};

export default function Home() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  // Staged settings — applied on "Run" click so charts don't recompute on every
  // slider move. Each group has "pending" (what the form shows) and "applied"
  // (what the charts use).
  const [pendingA, setPendingA] = useState<GroupSettingsType>(DEFAULT_A);
  const [pendingB, setPendingB] = useState<GroupSettingsType>(DEFAULT_B);
  const [appliedA, setAppliedA] = useState<GroupSettingsType>(DEFAULT_A);
  const [appliedB, setAppliedB] = useState<GroupSettingsType>(DEFAULT_B);

  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    fetchConfig()
      .then((cfg) => {
        setConfig(cfg);
        // Filter defaults to only available datasets
        const available = cfg.datasets.filter((d) => cfg.dataset_availability[d]);
        setPendingA((s) => ({
          ...s,
          selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        }));
        setPendingB((s) => ({
          ...s,
          selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        }));
        setAppliedA((s) => ({
          ...s,
          selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        }));
        setAppliedB((s) => ({
          ...s,
          selectedDatasets: s.selectedDatasets.filter((d) => available.includes(d)),
        }));
      })
      .catch((e) => setConfigError(e.message));
  }, []);

  if (configError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 font-medium mb-2">Could not connect to backend</p>
          <p className="text-sm text-gray-500">{configError}</p>
          <p className="text-sm text-gray-500 mt-1">
            Make sure the FastAPI server is running on{" "}
            {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
          </p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* ── Sidebar ── */}
      <aside
        className={`
          flex-shrink-0 bg-white border-r border-gray-200 overflow-y-auto
          transition-all duration-200
          ${sidebarOpen ? "w-72" : "w-0 overflow-hidden"}
        `}
      >
        <div className="p-4 min-w-72">
          <h2 className="font-bold text-gray-800 text-base mb-1">Dashboard Settings</h2>
          <p className="text-xs text-gray-500 mb-4">
            Configure each group independently, then click Run to update charts.
          </p>

          <GroupSettings
            groupId="A"
            color="#3a5f83"
            settings={pendingA}
            config={config}
            onChange={setPendingA}
          />

          <hr className="my-4 border-gray-200" />

          <GroupSettings
            groupId="B"
            color="#4a7c6f"
            settings={pendingB}
            config={config}
            onChange={setPendingB}
          />

          <div className="mt-5 sticky bottom-0 bg-white pb-2 pt-1">
            <button
              onClick={() => {
                setAppliedA(pendingA);
                setAppliedB(pendingB);
              }}
              className="w-full bg-gray-800 hover:bg-gray-700 text-white text-sm font-semibold rounded py-2 transition-colors"
            >
              Run
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto">
        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-5 py-3 flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="text-gray-500 hover:text-gray-800 transition-colors text-lg"
            title="Toggle sidebar"
          >
            ☰
          </button>
          <div>
            <h1 className="font-bold text-gray-900 text-lg leading-tight">
              Automation Exposure Analysis
            </h1>
            <p className="text-xs text-gray-500">
              Compare automation exposure across datasets, geographies, and aggregation levels.
            </p>
          </div>
        </div>

        {/* Charts — two columns */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 p-5">
          <GroupPanel
            groupId="A"
            color="#3a5f83"
            settings={appliedA}
            config={config}
          />
          <GroupPanel
            groupId="B"
            color="#4a7c6f"
            settings={appliedB}
            config={config}
          />
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-gray-200 mt-4">
          <p className="text-xs text-gray-400">
            Dashboard built for the Anthropic Economic Index (AEI) project. Source: 2025 O*NET task
            data, 2024 BLS OEWS employment & wage data, AEI conversation data, MCP server
            classification pipeline.
          </p>
        </div>
      </main>
    </div>
  );
}
