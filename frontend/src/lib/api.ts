import type {
  GroupSettings,
  ComputeResponse,
  ConfigResponse,
  WorkActivitiesResponse,
  TrendsResponse,
  TrendsSettings,
  WATrendsSettings,
  OccupationSummary,
  OccupationTasksResponse,
  ExplorerGroupsResponse,
  WAExplorerResponse,
  WATasksResponse,
  TaskChangesResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchConfig(): Promise<ConfigResponse> {
  const res = await fetch(`${API_BASE}/api/config`);
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

export async function fetchCompute(settings: GroupSettings): Promise<ComputeResponse> {
  const res = await fetch(`${API_BASE}/api/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_datasets: settings.selectedDatasets,
      combine_method:    settings.combineMethod,
      method:            settings.method,
      use_auto_aug:      settings.useAutoAug,

      physical_mode:     settings.physicalMode,
      geo:               settings.geo,
      agg_level:         settings.aggLevel,
      sort_by:           settings.sortBy,
      top_n:             settings.topN,
      search_query:      settings.searchQuery ?? "",
      context_size:      settings.contextSize ?? 5,
    }),
  });
  if (!res.ok) throw new Error("Compute request failed");
  return res.json();
}

export async function fetchWorkActivities(settings: GroupSettings): Promise<WorkActivitiesResponse> {
  const res = await fetch(`${API_BASE}/api/work-activities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      selected_datasets: settings.selectedDatasets,
      combine_method:    settings.combineMethod,
      method:            settings.method,
      use_auto_aug:      settings.useAutoAug,

      physical_mode:     settings.physicalMode,
      geo:               settings.geo,
      agg_level:         settings.aggLevel,
      sort_by:           settings.sortBy,
      top_n:             settings.topN,
      search_query:      settings.searchQuery ?? "",
      context_size:      settings.contextSize ?? 5,
    }),
  });
  if (!res.ok) throw new Error("Work activities request failed");
  return res.json();
}

export async function fetchTrends(settings: TrendsSettings): Promise<TrendsResponse> {
  const res = await fetch(`${API_BASE}/api/trends`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      series:        settings.series,
      method:        settings.method,
      use_auto_aug:  settings.useAutoAug,

      physical_mode: settings.physicalMode,
      geo:           settings.geo,
      agg_level:     settings.aggLevel,
      top_n:         settings.topN,
      sort_by:       settings.sortBy,
    }),
  });
  if (!res.ok) throw new Error("Trends request failed");
  return res.json();
}

export async function fetchWATrends(settings: WATrendsSettings): Promise<TrendsResponse> {
  const res = await fetch(`${API_BASE}/api/trends/work-activities`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      series:         settings.series,
      method:         settings.method,
      use_auto_aug:   settings.useAutoAug,

      physical_mode:  settings.physicalMode,
      geo:            settings.geo,
      top_n:          settings.topN,
      sort_by:        settings.sortBy,
      activity_level: settings.activityLevel,
    }),
  });
  if (!res.ok) throw new Error("WA Trends request failed");
  return res.json();
}

export async function fetchExplorerOccupations(): Promise<OccupationSummary[]> {
  const res = await fetch(`${API_BASE}/api/explorer`);
  if (!res.ok) throw new Error("Explorer request failed");
  const data = await res.json();
  return data.occupations;
}

export async function fetchOccupationTasks(title: string): Promise<OccupationTasksResponse> {
  const res = await fetch(
    `${API_BASE}/api/explorer/tasks?title=${encodeURIComponent(title)}`
  );
  if (!res.ok) throw new Error(`Tasks request failed for ${title}`);
  return res.json();
}

export async function fetchExplorerGroups(): Promise<ExplorerGroupsResponse> {
  const res = await fetch(`${API_BASE}/api/explorer/groups`);
  if (!res.ok) throw new Error("Explorer groups request failed");
  return res.json();
}

export async function fetchAllTasks(): Promise<{ tasks: import("./types").AllTaskRow[] }> {
  const res = await fetch(`${API_BASE}/api/explorer/all-tasks`);
  if (!res.ok) throw new Error("All tasks request failed");
  return res.json();
}

export async function fetchAllEcoTasks(): Promise<{ tasks: import("./types").EcoTaskRow[] }> {
  const res = await fetch(`${API_BASE}/api/explorer/all-eco-tasks`);
  if (!res.ok) throw new Error("All eco tasks request failed");
  return res.json();
}

export async function fetchWAExplorer(): Promise<WAExplorerResponse> {
  const res = await fetch(`${API_BASE}/api/explorer/wa`);
  if (!res.ok) throw new Error("WA Explorer request failed");
  return res.json();
}

export async function fetchWAActivityTasks(level: string, name: string): Promise<WATasksResponse> {
  const res = await fetch(
    `${API_BASE}/api/explorer/wa/tasks?level=${encodeURIComponent(level)}&name=${encodeURIComponent(name)}`
  );
  if (!res.ok) throw new Error(`WA tasks request failed for ${level}/${name}`);
  return res.json();
}

export async function fetchTaskChanges(fromDataset: string, toDataset: string): Promise<TaskChangesResponse> {
  const res = await fetch(`${API_BASE}/api/task-changes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from_dataset: fromDataset, to_dataset: toDataset }),
  });
  if (!res.ok) throw new Error("Task changes request failed");
  return res.json();
}
