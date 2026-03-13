// ── Overview ──────────────────────────────────────────────────────────────────

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
  dataset_series: Record<string, string[]>;
  agg_levels: Record<string, string>;
  sort_options: string[];
  crosswalk_available: boolean;
  eco2015_available: boolean;
}

// ── Work Activities ───────────────────────────────────────────────────────────

export interface ActivityRow {
  category: string;
  pct_tasks_affected: number;
  workers_affected: number;
  wages_affected: number;
}

export interface ActivityGroup {
  datasets: string[];
  gwa: ActivityRow[];
  iwa: ActivityRow[];
  dwa: ActivityRow[];
}

export interface WorkActivitiesResponse {
  aei_group?: ActivityGroup;
  mcp_group?: ActivityGroup;
}

// ── Trends ────────────────────────────────────────────────────────────────────

export interface TrendRow {
  category: string;
  pct_tasks_affected: number;
  workers_affected: number;
  wages_affected: number;
}

export interface TrendDataPoint {
  dataset: string;
  date: string;
  rows: TrendRow[];
}

export interface TrendSeries {
  name: string;
  data_points: TrendDataPoint[];
  top_categories: string[];
  group_col: string;
}

export interface TrendsResponse {
  series: TrendSeries[];
}

export interface TrendsSettings {
  series: string[];
  method: "freq" | "imp";
  useAutoAug: boolean;
  useAdjMean: boolean;
  physicalMode: "all" | "exclude" | "only";
  geo: "nat" | "ut";
  aggLevel: "major" | "minor" | "broad" | "occupation";
  topN: number;
  sortBy: string;
}

// ── Explorer ──────────────────────────────────────────────────────────────────

export interface OccupationSummary {
  title_current: string;
  major?: string;
  minor?: string;
  broad?: string;
  emp_nat?: number;
  emp_ut?: number;
  wage_nat?: number;
  wage_ut?: number;
  n_tasks: number;
  avg_auto_aug_aei?: number;
  avg_auto_aug_mcp?: number;
  avg_auto_aug_ms?: number;
  avg_pct_norm_aei?: number;
  avg_pct_norm_mcp?: number;
  avg_pct_norm_ms?: number;
}

export interface TaskDetail {
  task: string;
  task_normalized: string;
  dwa_title?: string;
  iwa_title?: string;
  gwa_title?: string;
  freq_mean?: number;
  importance?: number;
  relevance?: number;
  aei?: { auto_aug_mean?: number; pct_normalized?: number } | null;
  mcp?: { auto_aug_mean_adj?: number; pct_normalized?: number } | null;
  microsoft?: { auto_aug_mean?: number; pct_normalized?: number } | null;
  avg_auto_aug?: number;
  max_auto_aug?: number;
  avg_pct_normalized?: number;
  max_pct_normalized?: number;
}

export interface OccupationTasksResponse {
  title: string;
  tasks: TaskDetail[];
}
