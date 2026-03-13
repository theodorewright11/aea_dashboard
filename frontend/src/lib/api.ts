import type { GroupSettings, ComputeResponse, ConfigResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchConfig(): Promise<ConfigResponse> {
  const res = await fetch(`${API_BASE}/api/config`);
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

export async function fetchCompute(
  settings: GroupSettings
): Promise<ComputeResponse> {
  const res = await fetch(`${API_BASE}/api/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_datasets: settings.selectedDatasets,
      combine_method: settings.combineMethod,
      method: settings.method,
      use_auto_aug: settings.useAutoAug,
      use_adj_mean: settings.useAdjMean,
      physical_mode: settings.physicalMode,
      geo: settings.geo,
      agg_level: settings.aggLevel,
      sort_by: settings.sortBy,
      top_n: settings.topN,
    }),
  });
  if (!res.ok) throw new Error("Compute request failed");
  return res.json();
}
