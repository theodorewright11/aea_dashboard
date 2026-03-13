"use client";

import { useEffect, useState, useCallback } from "react";
import type { GroupSettings, ChartRow, ConfigResponse } from "@/lib/types";
import { fetchCompute } from "@/lib/api";
import HorizontalBarChart from "./HorizontalBarChart";

interface Props {
  groupId: "A" | "B";
  color: string;
  settings: GroupSettings;
  config: ConfigResponse;
}

function buildSubtitle(settings: GroupSettings): string {
  const names = settings.selectedDatasets;
  if (!names.length) return "No datasets selected";
  let label = names.join(" + ");
  if (names.length > 1) label += ` (${settings.combineMethod})`;
  const methodStr = settings.method === "freq" ? "Freq" : "Imp";
  const geoStr = settings.geo === "nat" ? "National" : "Utah";
  const aggMap: Record<string, string> = {
    major: "Major Category",
    minor: "Minor Category",
    broad: "Broad Occupation",
    occupation: "Occupation",
  };
  const extras: string[] = [];
  if (settings.useAutoAug) extras.push("auto-aug");
  if (settings.physicalMode !== "all") extras.push(settings.physicalMode);
  const extrasStr = extras.length ? `  ·  ${extras.join(", ")}` : "";
  return `${label}  ·  ${methodStr}  ·  ${geoStr}  ·  ${aggMap[settings.aggLevel]}${extrasStr}  ·  Top ${settings.topN}`;
}

export default function GroupPanel({ groupId, color, settings, config }: Props) {
  const [rows, setRows] = useState<ChartRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!settings.selectedDatasets.length) {
      setRows([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchCompute(settings);
      setRows(resp.rows);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load data");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [settings]);

  useEffect(() => {
    load();
  }, [load]);

  const subtitle = buildSubtitle(settings);

  return (
    <div className="flex flex-col gap-4">
      {/* Group header banner */}
      <div
        className="rounded px-4 py-2 text-white text-base font-bold"
        style={{ backgroundColor: color }}
      >
        Group {groupId}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: color }} />
          <span className="ml-3 text-sm text-gray-500">Computing…</span>
        </div>
      )}

      {error && (
        <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Error: {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <HorizontalBarChart
            rows={rows ?? []}
            metric="workers"
            color={color}
            subtitle={subtitle}
          />
          <HorizontalBarChart
            rows={rows ?? []}
            metric="wages"
            color={color}
            subtitle={subtitle}
          />
          <HorizontalBarChart
            rows={rows ?? []}
            metric="tasks"
            color={color}
            subtitle={subtitle}
          />
        </>
      )}
    </div>
  );
}
