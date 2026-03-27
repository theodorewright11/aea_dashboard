// ── Overview ──────────────────────────────────────────────────────────────────

export interface GroupSettings {
  selectedDatasets: string[];
  combineMethod: "Average" | "Max";
  method: "freq" | "imp";
  useAutoAug: boolean;
  physicalMode: "all" | "exclude" | "only";
  geo: "nat" | "ut";
  aggLevel: "major" | "minor" | "broad" | "occupation";
  sortBy: string;
  topN: number;
  searchQuery?: string;
  contextSize?: number;
}

export interface ChartRow {
  category: string;
  pct_tasks_affected: number;
  workers_affected: number;
  wages_affected: number;
  rank_workers: number;
  rank_wages: number;
  rank_pct: number;
}

export interface ComputeResponse {
  rows: ChartRow[];
  group_col: string;
  total_categories: number;
  total_emp: number;
  total_wages: number;
  matched_category?: string | null;
}

export interface ConfigResponse {
  datasets: string[];
  dataset_availability: Record<string, boolean>;
  dataset_series: Record<string, string[]>;
  agg_levels: Record<string, string>;
  sort_options: string[];
  crosswalk_available: boolean;
  eco2015_available: boolean;
  aei_conv_snapshot_datasets: string[];
  aei_api_snapshot_datasets: string[];
  aei_conv_cumulative_datasets: string[];
  aei_api_cumulative_datasets: string[];
  aei_both_cumulative_datasets: string[];
  mcp_datasets: string[];
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
  physicalMode: "all" | "exclude" | "only";
  geo: "nat" | "ut";
  aggLevel: "major" | "minor" | "broad" | "occupation";
  topN: number;
  sortBy: string;
}

export interface WATrendsSettings {
  series: string[];
  method: "freq" | "imp";
  useAutoAug: boolean;
  physicalMode: "all" | "exclude" | "only";
  geo: "nat" | "ut";
  topN: number;
  sortBy: string;
  activityLevel: "gwa" | "iwa" | "dwa";
}

// ── Explorer shared metrics ───────────────────────────────────────────────────

export interface ExplorerMetrics {
  n_tasks: number;
  n_physical_tasks: number;
  pct_physical?: number | null;
  auto_avg_with_vals?: number | null;
  auto_max_with_vals?: number | null;
  auto_avg_all?: number | null;
  auto_max_all?: number | null;
  pct_avg_with_vals?: number | null;
  pct_max_with_vals?: number | null;
  pct_avg_all?: number | null;
  pct_max_all?: number | null;
  sum_pct_avg?: number | null;
  sum_pct_max?: number | null;
}

// ── Explorer — Occupations ────────────────────────────────────────────────────

export interface OccupationSummary extends ExplorerMetrics {
  title_current: string;
  major?: string;
  minor?: string;
  broad?: string;
  emp_nat?: number;
  emp_ut?: number;
  wage_nat?: number;
  wage_ut?: number;
}

export interface TaskSourceStats {
  auto_aug?: number | null;
  pct_norm?: number | null;
}

export interface McpEntry {
  title: string;
  rating?: number | null;
  url?: string | null;
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
  physical?: boolean | null;
  sources: Record<string, TaskSourceStats>;
  avg_auto_aug?: number | null;
  max_auto_aug?: number | null;
  avg_pct_norm?: number | null;
  max_pct_norm?: number | null;
  top_mcps?: McpEntry[];
}

export interface OccupationTasksResponse {
  title: string;
  tasks: TaskDetail[];
}

// ── Explorer — Groups (major/minor/broad level pre-computed) ──────────────────

export interface ExplorerGroupRow extends ExplorerMetrics {
  name: string;
  parent?: string | null;
  grandparent?: string | null;
  emp_nat?: number | null;
  emp_ut?: number | null;
  wage_nat?: number | null;
  wage_ut?: number | null;
  n_occs: number;
}

export interface ExplorerGroupsResponse {
  major: ExplorerGroupRow[];
  minor: ExplorerGroupRow[];
  broad: ExplorerGroupRow[];
}

// ── Explorer — All Tasks ──────────────────────────────────────────────────────

export interface AllTaskRow {
  task: string;
  task_normalized: string;
  dwa_title?: string | null;
  iwa_title?: string | null;
  gwa_title?: string | null;
  physical?: boolean | null;
  n_occs: number;
  emp_nat?: number | null;
  emp_ut?: number | null;
  wage_nat?: number | null;
  sources: Record<string, TaskSourceStats>;
  avg_auto_aug?: number | null;
  max_auto_aug?: number | null;
  avg_pct_norm?: number | null;
  max_pct_norm?: number | null;
}

// ── Explorer — All Eco Task Rows (one per task×occ) ──────────────────────────

export interface EcoTaskRow {
  task: string;
  task_normalized: string;
  title_current: string;
  broad_occ?: string | null;
  minor_occ_category?: string | null;
  major_occ_category?: string | null;
  dwa_title?: string | null;
  iwa_title?: string | null;
  gwa_title?: string | null;
  physical?: boolean | null;
  emp_nat?: number | null;
  emp_ut?: number | null;
  wage_nat?: number | null;
  wage_ut?: number | null;
  emp_nat_freq?: number | null;
  emp_ut_freq?: number | null;
  emp_nat_value?: number | null;
  emp_ut_value?: number | null;
  freq_mean?: number | null;
  importance?: number | null;
  relevance?: number | null;
  sources: Record<string, TaskSourceStats>;
  avg_auto_aug?: number | null;
  max_auto_aug?: number | null;
  avg_pct_norm?: number | null;
  max_pct_norm?: number | null;
  top_mcps?: McpEntry[];
}

// ── WA Explorer ───────────────────────────────────────────────────────────────

export interface WAExplorerRow extends ExplorerMetrics {
  level: "gwa" | "iwa" | "dwa";
  name: string;
  parent?: string | null;
  gwa?: string | null;
  emp_nat_freq?: number | null;
  emp_ut_freq?: number | null;
  emp_nat_value?: number | null;
  emp_ut_value?: number | null;
  wage_nat_freq?: number | null;
  wage_ut_freq?: number | null;
  wage_nat_value?: number | null;
  wage_ut_value?: number | null;
  n_occs: number;
}

export interface WAExplorerResponse {
  rows: WAExplorerRow[];
}

export interface WATaskDetail {
  task: string;
  task_normalized: string;
  dwa_title?: string | null;
  iwa_title?: string | null;
  gwa_title?: string | null;
  physical?: boolean | null;
  emp_nat_freq?: number | null;
  emp_ut_freq?: number | null;
  emp_nat_value?: number | null;
  emp_ut_value?: number | null;
  wage_nat_freq?: number | null;
  wage_nat_value?: number | null;
  freq_mean?: number | null;
  importance?: number | null;
  relevance?: number | null;
  title_current?: string | null;
  broad_occ?: string | null;
  minor_occ_category?: string | null;
  major_occ_category?: string | null;
  sources: Record<string, TaskSourceStats>;
  avg_auto_aug?: number | null;
  max_auto_aug?: number | null;
  avg_pct_norm?: number | null;
  max_pct_norm?: number | null;
  top_mcps?: McpEntry[];
}

export interface WATasksResponse {
  level: string;
  name: string;
  tasks: WATaskDetail[];
}

// ── Task Changes ─────────────────────────────────────────────────────────────

export type TaskChangeStatus = "new" | "removed" | "changed" | "unchanged" | "not_in_baseline";

export interface TaskChangeRow {
  task: string;
  task_normalized: string;
  title_current: string;
  broad_occ?: string | null;
  minor_occ_category?: string | null;
  major_occ_category?: string | null;
  dwa_title?: string | null;
  iwa_title?: string | null;
  gwa_title?: string | null;
  physical?: boolean | null;
  freq_mean?: number | null;
  importance?: number | null;
  relevance?: number | null;
  emp_nat?: number | null;
  emp_ut?: number | null;
  wage_nat?: number | null;
  wage_ut?: number | null;
  status: TaskChangeStatus;
  from_auto_aug?: number | null;
  to_auto_aug?: number | null;
  delta_auto_aug?: number | null;
  from_pct?: number | null;
  to_pct?: number | null;
  delta_pct?: number | null;
  sources: Record<string, TaskSourceStats>;
  avg_auto_aug?: number | null;
  max_auto_aug?: number | null;
  avg_pct_norm?: number | null;
  max_pct_norm?: number | null;
  top_mcps?: McpEntry[];
}

export interface TaskChangesResponse {
  rows: TaskChangeRow[];
  from_dataset: string;
  to_dataset: string;
}
