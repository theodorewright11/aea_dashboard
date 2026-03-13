export interface GroupSettings {
  selectedDatasets: string[];
  combineMethod: "Average" | "Max";
  method: "freq" | "imp";
  useAutoAug: boolean;
  useAdjMean: boolean;
  physicalMode: "all" | "exclude" | "only";
  geo: "nat" | "ut";
  aggLevel: "major" | "minor" | "broad" | "occupation";
  sortBy: string;
  topN: number;
}

export interface ChartRow {
  category: string;
  pct_tasks_affected: number;
  workers_affected: number;
  wages_affected: number;
}

export interface ComputeResponse {
  rows: ChartRow[];
  group_col: string;
}

export interface ConfigResponse {
  datasets: string[];
  dataset_availability: Record<string, boolean>;
  agg_levels: Record<string, string>; // display label → internal key
  sort_options: string[];
  crosswalk_available: boolean;
}
