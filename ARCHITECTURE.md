# ARCHITECTURE.md — AEA Dashboard

Dense technical reference for how the system is built. Read this before making changes.
Paired with [PRD.md](PRD.md) (product spec) and [CLAUDE.md](CLAUDE.md) (agent behavior rules).

---

## 1. System Overview

**Stack:** FastAPI (Python 3.12) backend + Next.js 14 / React 18 / TypeScript frontend.
**Deployment:** Railway (backend via Docker) + Vercel (frontend static/SSR).

```
aea_dashboard/
├── backend/
│   ├── main.py          — FastAPI app, all API endpoints + Pydantic models
│   ├── compute.py       — Core compute engine (all data processing)
│   └── config.py        — Dataset registry, paths, constants
├── frontend/
│   ├── src/
│   │   ├── app/                    — Next.js pages (one dir per route)
│   │   ├── components/             — Reusable React components
│   │   └── lib/                    — Types, API client, utilities
│   ├── tailwind.config.ts
│   └── package.json
├── data/                — CSV data files (see §2)
├── analysis/            — Offline CSV generation scripts
├── Dockerfile           — Backend: python:3.12-slim, copies backend/ + data/, runs uvicorn
├── railway.json         — {"build": {"builder": "DOCKERFILE"}}
└── requirements.txt     — fastapi, uvicorn, pandas, numpy
```

### Running Locally

```bash
# Backend
venv/Scripts/python -m uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm run dev    # http://localhost:3000
```

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`.

---

## 2. Data Files

All CSVs live in `data/`. There are two SOC taxonomies in play:
- **2010 SOC** — used by AEI and ECO 2015. Occupation column: `title`.
- **2019 SOC** — used by MCP, Microsoft, and ECO 2025. Occupation column: `title_current`.

### Dataset Registry

| Dataset | File | SOC | `is_aei` | `is_mcp` | Notes |
|---------|------|-----|----------|----------|-------|
| AEI v1–v4 | `final_aei_v{1..4}.csv` | 2010 | true | false | Snapshot; needs crosswalk to 2019 |
| AEI API v3–v4 | `final_aei_api_v{3,4}.csv` | 2010 | true | false | Snapshot; needs crosswalk to 2019 |
| AEI Cumul. v1–v4 | `final_aei_cumulative_v{1..4}.csv` | 2010 | true | false | Cumulative (each version accumulates all prior); needs crosswalk. Only one at a time; cannot mix with snapshot AEI. |
| MCP v1–v4 | `final_mcp_v{1..4}.csv` | 2019 | false | true | Has `auto_aug_mean_adj`; only one version at a time |
| Microsoft | `final_microsoft.csv` | 2019 | false | false | Single snapshot |

**Dataset families in `config.py`:**
- `AEI_SNAPSHOT_DATASETS` — `{"AEI v1", "AEI v2", "AEI v3", "AEI v4", "AEI API v3", "AEI API v4"}`
- `AEI_CUMULATIVE_DATASETS` — `{"AEI Cumul. v1", ..., "AEI Cumul. v4"}`
- `MCP_DATASETS` — `{"MCP v1", ..., "MCP v4"}`

These sets are exposed via `GET /api/config` as `aei_snapshot_datasets`, `aei_cumulative_datasets`, `mcp_datasets` and consumed by `frontend/src/lib/datasetRules.ts` for selection enforcement (see §6).

### Baseline Files (not user-selectable)

| File | Purpose |
|------|---------|
| `final_eco_2025.csv` (~23,850 rows) | Primary ECO baseline (denominator for all metrics). Has `task_prop`, `title_current` (2019 SOC). |
| `final_eco_2015.csv` (~24,631 rows) | AEI work-activity baseline. Has `title` (2010 SOC). |
| `2010_to_2019_soc_crosswalk.csv` | Maps 2010 SOC → 2019 SOC. Searched in `data/`, then `../aea_dashboard_dev/data/`, then `../automation_exposure_analysis/data/`. |

### Shared Columns Across All Datasets

| Column | Type | Description |
|--------|------|-------------|
| `task`, `task_normalized` | str | O*NET task text (raw and normalized) |
| `dwa_title`, `iwa_title`, `gwa_title` | str | O*NET work activity hierarchy |
| `freq_mean` | 0–10 | Task frequency (O*NET survey) |
| `importance` | 0–5 | Task importance (O*NET survey) |
| `relevance` | 0–100 | Task relevance (O*NET survey) |
| `auto_aug_mean` | 0–5 | AI automatability score |
| `auto_aug_mean_adj` | 0–5 | MCP only — excludes flagged ratings |
| `pct_normalized` | float | Share of AI conversations involving this task. **Already in percent form** (0.4 = 0.4%, NOT 40%) |
| `physical` | bool | Truly physical task |
| `date` | str | Dataset snapshot date |
| `emp_tot_nat_2024`, `emp_tot_ut_2024` | float | BLS OEWS 2024 employment |
| `a_med_nat_2024`, `a_med_ut_2024` | float | BLS OEWS 2024 median annual wage |
| `task_prop` | float | ECO 2025 only — ratio of 2025/2015 tasks per occupation |
| `soc_code_2010` | str | AEI datasets only — used for crosswalk |

### Dataset Dates (for Trends)

| Dataset | Date |
|---------|------|
| AEI v1 | 2024-12-23 |
| AEI v2 | 2025-03-06 |
| AEI v3 | 2025-08-11 |
| AEI v4 | 2025-11-13 |
| AEI API v3 | 2025-08-11 |
| AEI API v4 | 2025-11-13 |
| MCP v1 | 2025-04-24 |
| MCP v2 | 2025-05-24 |
| MCP v3 | 2025-07-23 |
| MCP v4 | 2026-02-18 |
| Microsoft | 2024-09-30 |

**ECO 2015 note:** `auto_aug_mean` and `pct_normalized` are all null/zero in eco files — values must come from AI datasets.

---

## 3. Backend Module Structure

### `config.py` — Registry & Constants

```python
DATASETS           # dict[str, {file, is_aei, is_mcp}] — 15 selectable datasets (11 original + 4 cumulative AEI)
ECO_2015_META      # internal-only baseline for AEI work-activity analysis
AEI_SNAPSHOT_DATASETS    # set of snapshot AEI names: {AEI v1..v4, AEI API v3..v4}
AEI_CUMULATIVE_DATASETS  # set of cumulative AEI names: {AEI Cumul. v1..v4}
MCP_DATASETS       # set of MCP names: {MCP v1..v4}
DATASET_SERIES     # {"AEI": ["AEI v1"..v4], "AEI API": [...], "AEI Cumul.": [...], "MCP": [...], "Microsoft": [...]}
AGG_LEVEL_COL      # {"major": "major_occ_category", "minor": "minor_occ_category",
                   #  "broad": "broad_occ", "occupation": "title_current"}
AGG_LEVEL_OPTIONS  # human-readable → key mapping
SORT_COL_MAP       # {"Workers Affected": "workers_affected", ...}
```

### `compute.py` — Compute Engine

Organized by pipeline stage:

#### Stage 1: Data Loading & Caching
- `load_eco_raw()` → cached `pd.DataFrame` from `final_eco_2025.csv`
- `load_eco2015_raw()` → cached `pd.DataFrame` from `final_eco_2015.csv`
- `load_crosswalk()` → cached crosswalk DataFrame (searches multiple paths)
- `crosswalk_available()`, `eco2015_available()`, `dataset_exists()` — availability checks

#### Stage 2: Task-Level Transformations
- `apply_physical_filter(df, mode)` — filters rows by `physical` column (`"all"` / `"exclude"` / `"only"`)
- `compute_task_comp(df, method, use_auto_aug, use_adj_mean)` → `pd.Series` of task completion weights
- `dedup_and_compute(df, title_col, emp_col, wage_col, method, ...)` — deduplicates on `(title, task_normalized)`, computes `task_comp`

#### Stage 3: ECO Baseline
- `load_eco_baseline(method, physical_mode, geo)` — deduped eco_2025 with task_comp computed (no auto_aug). Cached by `(method, physical_mode, geo)`.

#### Stage 4: Single-Dataset Compute
- `compute_single_dataset(file_path, is_aei, method, use_auto_aug, use_adj_mean, physical_mode, geo, agg_level)` — full pipeline for one AI dataset. If AEI: runs crosswalk pipeline (§4.3). If MCP/MS: dedup + compute directly. Calls `aggregate_results()` at the end. Cached by full parameter tuple.

#### Stage 5: Aggregation
- `aggregate_results(ai_df, eco_df, title_col, agg_level, emp_col, wage_col)` — computes pct/workers/wages at occupation level, then rolls up to requested agg_level. Also computes rank columns.

#### Stage 6: Multi-Dataset Combination
- `combine_results(results, group_col, combine_method)` — outer-joins multiple DataFrames, applies Average or Max per metric column.

#### Stage 7: Orchestration
- `get_group_data(settings)` — orchestrates the full pipeline for one sidebar group. Returns top-N or search-windowed rows plus `total_categories`, `total_emp`, `total_wages`, `matched_category`.
- `compute_work_activities(settings)` — splits datasets into AEI group (eco_2015 baseline) and MCP/MS group (eco_2025 baseline). Calls `_compute_wa_for_group()` for each.
- `compute_trends(settings)` — for each series family, runs `compute_single_dataset` for every version, records date, returns time series.
- `compute_wa_trends(settings)` — same but for work activities, using `_compute_wa_for_group()` per dataset version.

#### Stage 8: Explorer
- `_build_explorer_task_lookup()` — builds `task_normalized → {source_name: {auto_aug, pct_norm}}` across all 8 sources. AEI values averaged across 2010 SOC titles. MCP uses `auto_aug_mean_adj`. Cached.
- `_compute_task_metrics(task_norms, lookup)` — given task list + lookup, returns 10 metric fields (§4.6).
- `get_explorer_occupations()` — 923 occupation summaries with hierarchy, emp, wages, 10 metrics. Cached.
- `get_explorer_groups()` — pre-computed major/minor/broad aggregations (unique task_norms per group, not averages of occ-level values). Cached.
- `get_occupation_tasks(title)` — task details for one occupation (all 8 sources). Cached per title.
- `get_all_tasks()` — all unique tasks (deduplicated by `task_normalized`) with metrics + allocated emp/wage. Cached.
- `get_all_eco_task_rows()` — all ~23,850 rows from eco_2025 (each task × occupation combination) with occupation hierarchy, raw emp/wage, `n_tasks_per_occ`, and AI metrics from the task lookup. Cached. Used by both explorer task-level views.
- `get_wa_explorer_data()` — GWA/IWA/DWA rows with emp allocation + metrics. Cached.
- `get_wa_tasks_for_activity(level, name)` — task details for one WA activity.

### `main.py` — API Layer

Pydantic request/response models + thin endpoint functions that call compute functions and serialize results. All float values sanitized through `_safe()` (NaN → 0.0) and `_safe_num()` (NaN/Inf → None). See §5 for full API contracts.

---

## 4. Computation Logic

### 4.1 Task Completion Weight

Two methods for computing a task's weight (`task_comp`):

```
Time method:        task_comp = freq_mean
Value method:       task_comp = freq_mean × relevance × importance
```

With auto-aug multiplier enabled:
```
task_comp = task_comp × (auto_aug_mean / 5)
```
For MCP datasets with `use_adj_mean=true`: uses `auto_aug_mean_adj` instead of `auto_aug_mean`.

The ECO baseline is always computed **without** auto-aug (it represents the total task profile).

### 4.2 Occupation-Level Metrics

```
pct_tasks_affected = Σ(AI task_comp) / Σ(ECO task_comp) × 100
```

This is a **ratio-of-totals** (not an average of per-task percentages). Clipped to [0, 100].

```
workers_affected = (pct_tasks_affected / 100) × emp
wages_affected   = (pct_tasks_affected / 100) × emp × median_wage
```

### 4.3 AEI Crosswalk Pipeline (2010 → 2019 SOC)

AEI datasets use 2010 SOC codes. The pipeline to convert:

1. **Dedup** AEI data on `(title, task_normalized)` and compute `task_comp`
2. **Join** crosswalk: `soc_code_2010` → `O*NET-SOC 2019 Title`
3. **Compute split_count**: number of distinct 2019 titles per 2010 code
4. **Divide** `task_comp` and `emp` by `split_count`
5. **Group by** `(O*NET-SOC 2019 Title, task_normalized)`: sum `task_comp`, sum `emp`
6. **Deflate by task_prop**: `task_comp /= task_prop` from eco_2025 (accounts for task set changes between 2015 and 2025). `task_prop` clipped to ≥ 1.0.
7. **Fill group columns** (broad_occ, minor_occ_category, major_occ_category) from eco_2025 where missing

### 4.4 Group-Level Aggregation

When `agg_level != "occupation"`:

- **pct_tasks_affected** is recomputed at the group level as `Σ(ai_task_comp in group) / Σ(eco_task_comp in group) × 100` — NOT averaged from occupation-level percentages
- **workers_affected** and **wages_affected** are summed from occupation-level values

Rank columns (`rank_workers`, `rank_wages`, `rank_pct`) are computed across ALL categories before top-N filtering. `total_emp` and `total_wages` are also economy-wide sums.

### 4.5 Work Activity Metrics (DWA/IWA/GWA)

Work activity computation uses a different pipeline than occupation-level:

**Baseline split:** AEI datasets use eco_2015 (2010 SOC); MCP/Microsoft use eco_2025 (2019 SOC). These cannot be mixed.

**Dedup strategy per activity level:**
- `n_tasks_per_occ` uses `(title, task_normalized)` dedup — for emp allocation
- Each activity level uses `(title, task_normalized, act_col)` dedup — preserves all DWA/IWA/GWA associations (a task can map to multiple DWAs)

**Emp allocation (weighted):**

Emp is allocated to tasks using a weighted split based on the selected method (previously was an equal split `emp / n_tasks`):

```
Time method (freq):   weight = freq_mean;   emp_per_task = (weight / Σweight_per_occ) × emp_occ
Value method:         weight = freq_mean × relevance × importance;   emp_per_task = (weight / Σweight_per_occ) × emp_occ
```

The backend computes BOTH freq and value weightings simultaneously for the WA explorer endpoints, returning dual field sets (`emp_nat_freq`, `emp_nat_value`, etc.) so the frontend can toggle without re-fetching.

**Per-task workers contribution:**
```
workers_contribution = (ai_tc / eco_tc) × emp_per_task
wages_contribution   = workers_contribution × median_wage
```

These are summed by activity group. Then:
```
pct_tasks_affected = Σ(ai_tc in activity) / Σ(eco_tc in activity) × 100
```

**Important:** A task mapping to multiple DWAs contributes its full emp allocation to each DWA independently (they represent different aspects of the work; this is not double-counting).

**Multi-dataset combination** within a group uses the same Average/Max logic as occupation-level, via `_combine_activity_dfs()`.

### 4.6 Explorer Metrics (`_compute_task_metrics`)

Given a set of `task_normalized` values and the lookup dict:

```
For each task:
  per_task_avg_auto = mean(non-null auto_aug values across all 8 sources)
  per_task_max_auto = max(non-null auto_aug values across all 8 sources)
  (same for pct_norm)

auto_avg_with_vals = mean(per_task_avg) over tasks WHERE per_task_avg is not null
auto_max_with_vals = mean(per_task_max) over tasks WHERE per_task_max is not null
auto_avg_all       = mean(per_task_avg OR 0) over ALL tasks
auto_max_all       = mean(per_task_max OR 0) over ALL tasks

pct_avg_with_vals, pct_max_with_vals — same pattern for pct_norm
pct_avg_all, pct_max_all             — same pattern

sum_pct_avg = sum(per_task_avg pct) over tasks with values
sum_pct_max = sum(per_task_max pct) over tasks with values
```

**Group-level metrics** (major/minor/broad/GWA/IWA/DWA): task_norms are collected as **unique values across all occupations/activities in the group** — not averaged from sub-group metric values.

### 4.7 Explorer Task Lookup

`_build_explorer_task_lookup()` reads all 8 AI sources:
- **AEI v1–v4 + AEI API v3–v4**: groups by `task_normalized`, takes mean of `auto_aug_mean` and `pct_normalized` across all 2010 SOC titles sharing that task
- **MCP v4**: uses `auto_aug_mean_adj` (not `auto_aug_mean`)
- **Microsoft**: uses `auto_aug_mean`

Result: `dict[task_normalized → dict[source_name → {auto_aug: float|None, pct_norm: float|None}]]`

### 4.8 Explorer Emp/Wage Allocation (All Tasks)

For the Task-level flat table (`get_all_tasks()`):
```
n_unique_tasks_per_occ = count of unique task_norms in that occ (from eco_2025)
emp_contrib_per_task   = emp_occ / n_unique_tasks_per_occ

emp_nat for a task = Σ(emp_contrib_per_task) across all occupations sharing that task
wage_nat           = employment-weighted median: Σ(emp_contrib × wage) / Σ(emp_contrib)
```

Same allocation logic used for WA Explorer rows.

### 4.8.1 All Eco Task Rows (`get_all_eco_task_rows()`)

For the Task-level view in both explorers, returns every row from eco_2025 (~23,850 rows) as a task × occupation combination. Each row includes:
- `task`, `task_normalized` — task text (properly cased) and dedup key
- `title_current`, `broad_occ`, `minor_occ_category`, `major_occ_category` — occupation hierarchy
- `dwa_title`, `iwa_title`, `gwa_title` — work activity hierarchy
- `physical` — physical task flag
- `emp_nat`, `emp_ut`, `wage_nat`, `wage_ut` — **raw** occupation-level BLS numbers (NOT divided by task count)
- `n_tasks_per_occ` — count of unique `task_normalized` values for this occupation (used by frontend to divide workers/wages affected)
- `freq_mean`, `importance`, `relevance` — O*NET survey measures read directly from eco_2025 rows
- `sources`, `avg_auto_aug`, `max_auto_aug`, `avg_pct_norm`, `max_pct_norm` — AI metrics from the task lookup

The frontend uses `n_tasks_per_occ` to compute per-task workers/wages affected: `workers_aff = (pct/100) × emp / n_tasks_per_occ`.

### 4.9 Trends

`compute_trends()` iterates over each series family (AEI, MCP, etc.), runs `compute_single_dataset()` for each version in the family, and records the date (read from the CSV's `date` column). Returns all rows (not just top-N) per data point so the frontend can filter.

`top_categories` is set from the last (most recent) dataset version — these are the reference categories for the series.

**Frontend filtering:** The backend receives series family names (e.g., `["AEI", "MCP"]`), computes all versions in those families, but the frontend filters `data_points` by `dp.dataset` matching user-selected individual datasets before building chart data.

**Cumulative max mode** (frontend): value at date T = max of all dataset values at dates ≤ T, tracked via a running-max Map that carries forward. The line never decreases.

### 4.10 Multi-Dataset Combination

`combine_results()` (occupation-level) and `_combine_activity_dfs()` (activity-level):

1. Rename metric columns with `_0`, `_1`, etc. suffixes
2. Outer-join all DataFrames on the group column
3. For each metric: take `max(axis=1)` or `mean(axis=1)` across the suffixed columns

### 4.11 Search / Context Window

Backend sorts all categories descending by the selected metric, finds the first case-insensitive `contains` match, slices `[idx - contextSize : idx + contextSize + 1]`, and returns `matched_category` in the response. The matched bar is highlighted orange in the chart.

---

## 5. API Contracts

### `GET /api/health`
Returns `{"status": "ok"}`.

### `GET /api/config`

Response:
```ts
{
  datasets: string[];                        // all dataset names (15: 11 original + 4 cumulative AEI)
  dataset_availability: Record<string, boolean>;
  dataset_series: Record<string, string[]>;  // {"AEI": ["AEI v1"..], "AEI Cumul.": [...], "MCP": [...], ...}
  agg_levels: Record<string, string>;        // {"Major Category": "major", ...}
  sort_options: string[];                    // ["Workers Affected", ...]
  crosswalk_available: boolean;
  eco2015_available: boolean;
  aei_snapshot_datasets: string[];          // names of all snapshot AEI datasets
  aei_cumulative_datasets: string[];        // names of all cumulative AEI datasets
  mcp_datasets: string[];                   // names of all MCP datasets
}
```

### `POST /api/compute`

Request body (`GroupSettingsModel`):
```ts
{
  selected_datasets: string[];        // e.g., ["AEI v4", "MCP v4"]
  combine_method: string;             // "Average" | "Max"
  method: string;                     // "freq" | "imp"
  use_auto_aug: boolean;
  use_adj_mean: boolean;
  physical_mode: string;              // "all" | "exclude" | "only"
  geo: string;                        // "nat" | "ut"
  agg_level: string;                  // "major" | "minor" | "broad" | "occupation"
  sort_by: string;                    // "Workers Affected" | "Wages Affected" | "% Tasks Affected"
  top_n: number;                      // 1–30
  search_query: string;               // optional text search
  context_size: number;               // ± rows around search match
}
```

Response:
```ts
{
  rows: Array<{
    category: string;
    pct_tasks_affected: number;
    workers_affected: number;
    wages_affected: number;
    rank_workers: number;             // rank across ALL categories (1 = highest)
    rank_wages: number;
    rank_pct: number;
  }>;
  group_col: string;                  // column name used for category
  total_categories: number;           // count before top-N/search filter
  total_emp: number;                  // sum of workers_affected across ALL categories
  total_wages: number;                // sum of wages_affected across ALL categories
  matched_category?: string | null;   // set when search_query matched
}
```

### `POST /api/work-activities`

Same request body as `/api/compute`.

Response:
```ts
{
  aei_group?: {                       // present if AEI datasets selected
    datasets: string[];
    gwa: ActivityRow[];
    iwa: ActivityRow[];
    dwa: ActivityRow[];
  };
  mcp_group?: {                       // present if MCP/Microsoft datasets selected
    datasets: string[];
    gwa: ActivityRow[];
    iwa: ActivityRow[];
    dwa: ActivityRow[];
  };
}
// ActivityRow = { category: string; pct_tasks_affected: number; workers_affected: number; wages_affected: number; }
```

### `POST /api/trends`

Request body (`TrendsRequest`):
```ts
{
  series: string[];                   // ["AEI", "MCP", "Microsoft"]
  method: string;
  use_auto_aug: boolean;
  use_adj_mean: boolean;
  physical_mode: string;
  geo: string;
  agg_level: string;
  top_n: number;
  sort_by: string;
}
```

Response:
```ts
{
  series: Array<{
    name: string;                     // series family name (e.g., "AEI")
    data_points: Array<{
      dataset: string;                // individual dataset (e.g., "AEI v2")
      date: string;                   // from CSV date column
      rows: TrendRow[];               // ALL categories, not just top-N
    }>;
    top_categories: string[];         // from latest dataset version
    group_col: string;
  }>;
}
```

### `POST /api/trends/work-activities`

Request body (`WATrendsRequest`):
```ts
{
  series: string[];
  method: string;
  use_auto_aug: boolean;
  use_adj_mean: boolean;
  physical_mode: string;
  geo: string;
  top_n: number;
  sort_by: string;
  activity_level: string;             // "gwa" | "iwa" | "dwa"
}
```

Response: same `TrendsResponse` shape as `/api/trends`.

### `GET /api/explorer`

Response:
```ts
{
  occupations: Array<{
    title_current: string;
    major?: string;
    minor?: string;
    broad?: string;
    emp_nat?: number;
    emp_ut?: number;
    wage_nat?: number;
    wage_ut?: number;
    n_tasks: number;
    n_physical_tasks: number;
    pct_physical?: number;            // 0–1 fraction (multiply × 100 for display)
    auto_avg_with_vals?: number;      // 10 explorer metric fields
    auto_max_with_vals?: number;
    auto_avg_all?: number;
    auto_max_all?: number;
    pct_avg_with_vals?: number;
    pct_max_with_vals?: number;
    pct_avg_all?: number;
    pct_max_all?: number;
    sum_pct_avg?: number;
    sum_pct_max?: number;
  }>;
}
```

### `GET /api/explorer/tasks?title=...`

Response:
```ts
{
  title: string;
  tasks: Array<{
    task: string;
    task_normalized: string;
    dwa_title?: string;
    iwa_title?: string;
    gwa_title?: string;
    freq_mean?: number;
    importance?: number;
    relevance?: number;
    physical?: boolean;
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;  // keyed by source name
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
  }>;
}
```

### `GET /api/explorer/groups`

Response:
```ts
{
  major: ExplorerGroupRow[];
  minor: ExplorerGroupRow[];
  broad: ExplorerGroupRow[];
}
// ExplorerGroupRow = { name, parent?, grandparent?, emp_nat/ut, wage_nat/ut, n_occs, n_tasks,
//                      n_physical_tasks, pct_physical, ...10 metric fields }
```

### `GET /api/explorer/all-tasks`

Response:
```ts
{
  tasks: Array<{
    task: string;
    task_normalized: string;
    dwa_title?: string;
    iwa_title?: string;
    gwa_title?: string;
    physical?: boolean;
    n_occs: number;
    emp_nat?: number;                 // allocated: Σ(emp_occ / n_unique_tasks) across sharing occs
    emp_ut?: number;
    wage_nat?: number;                // employment-weighted median
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
  }>;
}
```

### `GET /api/explorer/all-eco-tasks`

Returns all ~23,850 eco_2025 rows (one per task × occupation). Used by both explorer task-level views.

Response:
```ts
{
  tasks: Array<{
    task: string;
    task_normalized: string;
    title_current: string;             // occupation name
    broad_occ?: string;
    minor_occ_category?: string;
    major_occ_category?: string;
    dwa_title?: string;
    iwa_title?: string;
    gwa_title?: string;
    physical?: boolean;
    emp_nat?: number;                  // raw occupation emp (NOT divided)
    emp_ut?: number;
    wage_nat?: number;                 // raw occupation wage (NOT divided)
    wage_ut?: number;
    n_tasks_per_occ: number;           // unique task count for this occupation
    freq_mean?: number;                // O*NET task frequency (0–10)
    importance?: number;               // O*NET task importance (0–5)
    relevance?: number;                // O*NET task relevance (0–100)
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
  }>;
}
```

### `GET /api/explorer/wa`

Response:
```ts
{
  rows: Array<{
    level: "gwa" | "iwa" | "dwa";
    name: string;
    parent?: string;
    gwa?: string;
    emp_nat_freq?: number;            // freq-weighted emp allocation
    emp_ut_freq?: number;
    emp_nat_value?: number;           // value-weighted emp allocation (freq×rel×imp)
    emp_ut_value?: number;
    wage_nat_freq?: number;           // emp-weighted median wage (freq weighting)
    wage_ut_freq?: number;
    wage_nat_value?: number;          // emp-weighted median wage (value weighting)
    wage_ut_value?: number;
    n_occs: number;
    n_tasks: number;
    n_physical_tasks: number;
    pct_physical?: number;
    ...10 metric fields
  }>;
}
```

### `GET /api/explorer/wa/tasks?level=...&name=...`

Response:
```ts
{
  level: string;
  name: string;
  tasks: Array<{
    task: string;
    task_normalized: string;
    dwa_title?: string;
    iwa_title?: string;
    gwa_title?: string;
    physical?: boolean;
    emp_nat_freq?: number;            // freq-weighted emp allocation
    emp_ut_freq?: number;
    emp_nat_value?: number;           // value-weighted emp allocation
    emp_ut_value?: number;
    wage_nat_freq?: number;
    wage_nat_value?: number;
    freq_mean?: number;               // O*NET task frequency (0–10)
    importance?: number;              // O*NET task importance (0–5)
    relevance?: number;               // O*NET task relevance (0–100)
    title_current?: string;           // occupation name (first occ in group sharing this task)
    broad_occ?: string;
    minor_occ_category?: string;
    major_occ_category?: string;
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
    top_mcps?: Array<{ title: string; url?: string }>;
  }>;
}
```

---

## 6. Frontend Architecture

### Navigation & Layout

`Navigation.tsx` — fixed 56px nav bar (`var(--nav-height)`), 7 links: Occupation Explorer, Work Activities Explorer, Occupation Categories, Work Activities, Trends, Instructions, About. Active tab highlighted with brand color. Includes a **Simple/Advanced toggle** button (right side of nav). All pages render below with `paddingTop: var(--nav-height)`.

`Footer.tsx` — global footer displayed below all page content. Contains source attribution text and labeled links: Dashboard GitHub, MCP Classification GitHub, Data Merging GitHub (placeholder — repo not yet available), Research Paper (placeholder — not yet available), and a contact email link.

Root URL (`/`) redirects to `/explorer` (Occupation Explorer is the default landing page).

`layout.tsx` — root layout mounting `<SimpleModeProvider>` → `<Navigation />` + `{children}` + `<Footer />`.

### Simple/Advanced Mode (`lib/SimpleModeContext.tsx`)

React context + provider with localStorage persistence (key: `aea_simple_mode`). Exposes `{ isSimple: boolean, toggle: () => void }` via `useSimpleMode()` hook.

**Hydration safety:** initial render always uses `isSimple = false`; stored value loads on mount to avoid SSR mismatch.

Each page imports `useSimpleMode()` and conditionally:
- Hides/shows controls based on `isSimple`
- Overrides computation settings (datasets, method, physical, auto-aug) at run time
- Explorer pages auto-compute pct_tasks_affected via a `useEffect` when `isSimple` is true. Major category pills (occ explorer) and GWA pills (WA explorer) remain visible in simple mode
- Occupation Categories / Work Activities chart pages show single group (A only) in simple mode
- Trends pages remove "Individual" line mode option and auto-match value ranking to line mode

Advanced settings are preserved in state — toggling back to Advanced restores them.

### Design System

CSS variables in `globals.css`:
```
--brand: #1a6b5a         --brand-hover: #155749     --brand-light: #e8f5f1
--group-a: #3a5f83       --group-b: #4a7c6f
--bg-base: #f7f7f4       --bg-surface: #ffffff      --bg-sidebar: #fafaf8
--border: #e4e4de        --border-light: #eeeeea
--text-primary: #1a1a1a  --text-secondary: #5a5a5a  --text-muted: #9b9b9b
--nav-height: 56px
```

Utility classes: `.card`, `.pill`, `.btn-brand`, `.btn-ghost`, `.filter-chip`, `.tag`, `.tag-aei`, `.tag-mcp`, `.tag-ms`, `.tag-avg`, `.tag-max`.

### Page: Occupation Categories (`/occupation-categories` → `app/occupation-categories/page.tsx`)

**Two-group (A/B) comparison with staged settings.**

State model:
- `pendingA/B` — form state (`GroupPending` interface: datasets, method, geo, aggLevel, topN, sortBy, physicalMode, useAutoAug, useAdjMean, searchQuery, contextSize)
- `fullResponseA/B` — backend results (fetched with topN=1000)
- `displayResponseA/B` — client-side filtered (applied topN or search window via `applyClientFilter()`)
- `appliedPendingA/B` — snapshot at run time (for config summary in PNG downloads)
- `panelCollapsed` — settings sections collapse after Run

Key flow:
1. User configures settings in `pendingA/B`
2. "Run" → `fetchCompute(pendingToSettings(pendingA))` + `fetchCompute(pendingToSettings(pendingB))` in parallel (topN=1000)
3. Results stored in `fullResponseA/B`; client-side `displayResponseA/B` computed via useMemo with current topN/search
4. `GroupPanel` renders 3 `HorizontalBarChart` components per group
5. `otherResponse` passed to each chart for cross-group delta tooltips

Controls layout: Datasets / Display / Filtering sections collapse after Run. TopN + Search + Sort always visible.

### Page: Work Activities (`/work-activities`)

Same two-group layout as Occupation Categories. Key differences:
- `activityLevel` (gwa/iwa/dwa) instead of `aggLevel`
- AEI-family and MCP/Microsoft-family datasets cannot be mixed (client-side enforcement with warning)
- Fetch uses topN=999; backend returns all rows; client-side search/filter in `WorkActivitiesPanel`

### Page: Trends (`/trends`)

Thin wrapper that fetches config and renders `TrendsView`.

### Page: Explorer (`/explorer`)

Fetches `occupations`, `groups`, and `config` in parallel, passes to `ExplorerView`.

### Page: Work Activities Explorer (`/wa-explorer`)

Fetches WA explorer rows + config, passes to `WAExplorerView`.

### Component: `GroupPanel`

Pure renderer. Props: `groupId`, `color`, `response`, `otherResponse`, `loading`, `error`, `matchedCategory`, `configSummary`.

Renders 3 ChartCards (Workers Affected / Wages Affected / % Tasks Affected), each with a download button that calls `downloadChartAsPng()` with `configSummary` as footer text.

### Component: `HorizontalBarChart`

Recharts `BarChart` with `layout="vertical"` (horizontal bars).

Props: `rows`, `metric` ("workers"|"wages"|"tasks"), `color`, `totalCategories`, `totalEmp`, `totalWages`, `otherGroupRows`, `matchedCategory`.

- Rich tooltip: shows all 3 metrics, rank within economy, economy share %, delta vs other group (even for categories not in other group's visible top-N)
- Matched category bar: orange (#c05621), others dimmed
- Dynamic height: `max(180, n * rowPitch + 56)`

### Component: `WorkActivitiesPanel`

Pure renderer for work activity charts. Props include `otherResponse` and `otherActivityLevel` for cross-group tooltip comparison. Selects `aei_group` or `mcp_group` from response. Shows baseline note (ECO 2015 vs 2025). Client-side `applySearch()` finds match and slices ±contextSize.

**Rich tooltips** — same as `HorizontalBarChart`: hovering a bar shows all 3 metrics (Workers, Wages, % Tasks) with rank within the full activity set, economy share %, and delta vs the other group. Ranks and totals are computed from the full (pre-topN/search) row set.

### Component: `TrendsView`

Two tabs: **Occupation Categories** and **Work Activities**, each with independent controls.

**Dataset selection:** Individual dataset pills (not family toggles). Backend receives family names (derived via `getSeriesToFetch()`); frontend filters `data_points` by `dp.dataset` matching selected individual datasets.

**Three line modes:**
- `individual` — one line per (dataset × category); `buildIndividualData()` filters to selected datasets
- `average` — one line per category; values averaged across datasets present at each date
- `max` — cumulative running max per category; value at date T = max(all values at dates ≤ T); implemented via `runningMax` Map

**Sort modes:**
- By value: max or avg metric value per category across all data points
- By increase: first-to-last change per line (absolute or percentage)

**Hover + lock interaction:**
- `hoveredLine` + `lockedLine` states; `activeLine = lockedLine ?? hoveredLine`
- Active line: strokeWidth 3.5; dimmed: 1.5; normal: 2.5
- Clicking an activeDot toggles `lockedLine`; a `dotClickedRef` flag prevents the parent div's onClick from clearing the lock in the same tick
- **Frozen tooltip panel:** captures `lockedPos` (screen x/y) and `lockedDate`; renders a fixed `<div>` showing **all lines'** values at the locked date (sorted by value desc, scrollable via `maxHeight: 60vh; overflowY: auto`); clamped to window bounds. Clicking the frozen panel dismisses it.

**Controls:** Collapsible sections (Datasets / Display / Filtering); TopN, Sort, Search, Value ranking, and Context controls always visible (do not require a Run first).

**Custom `ChartLegend`:** Grid of colored squares, clickable (click = lock). Shows increase badge per item. Passed to `downloadChartAsPng()` as `legendItems`.

### Component: `ExplorerView`

Props: `occupations: OccupationSummary[]`, `groups: ExplorerGroupsResponse`, `config: ConfigResponse`.

**16-column flat table** with inline drilldown. No accordion.

Levels: Major / Minor / Broad / Occupation / Task. At "Task" level, data fetched from `/api/explorer/all-tasks` on first switch and cached.

**`FlatRow` interface:** holds all metric fields plus `sourceOccs: OccupationSummary[]` (for lazy drilldown) and `level`.

**Controls:**
- Multi-select major category pills (empty = all)
- Click-to-sort column headers (asc/desc toggle)
- Per-column ≥/≤ filter dropdowns (`ColumnFilterDropdown`)
- Search bar with level selector + text highlighting via `highlightText()`
- Avg/Max toggle (which auto_aug variant to display)
- Nat/Utah toggle for emp/wage
- Auto-aug min sliders (with_vals and all_tasks variants)
- Reset button

**Pagination:** `rowLimit` state (100 rows), "Load 100 more →" footer. Resets on level/filter/search/sort changes.

**Child rows:** `childRowCache` — pre-built `useMemo` Map keyed by `"level:name"` for O(1) lookups. Rebuilt when groups/occupations/geo change.

**Task expansion:** Clicking an occupation row fetches tasks via `fetchOccupationTasks()`. Task detail shows Occupation Classification (Broad → Minor → Major), Activity Classification (GWA/IWA/DWA), per-source breakdown table (AEI v1–v4, API v3–v4, MCP v4, Microsoft, plus AVG and MAX summary rows).

**`PctComputePanel`:** Collapsible panel calling `/api/compute` with `aggLevel: "occupation"`, `topN: 1000`. Returns `Map<string, number>` (title → pct_tasks_affected). Adds a `minPctAffected` slider filter to the table. **Auto-recomputes** when the parent `geo` changes while a previous compute result exists (via `geoChangedRef` + `useEffect`).

**Major category pills** are always visible (including in simple mode).

**Task expansion section order:** Occupation Categories → Work Activities → Task Detail → Source Breakdown → Top MCP Servers. Task-level task view shows physical/freq/imp/rel only (no auto/pct). Accordion task view shows the same plus auto avg/max and pct avg/max in a side table.

**Task-level columns:** `freq_mean`, `importance`, `relevance` are available as table columns at the task level only (`TASK_ONLY_COLS`), hidden in simple mode.

**`InfoTooltip`:** `createPortal(tooltip, document.body)` with `position: fixed` at mouse coords — avoids clipping by `overflow: hidden` ancestors.

**Formatters:**
- `fmtPctNorm(v)`: displays value directly as % (no ×100); `< 0.00001` → full decimal; `< 0.01` → `toPrecision(1)`; `≥ 0.01` → `toFixed(4)`
- `fmtAutoAug(v)`: `toFixed(3)`
- `fmtPctPhys(v)`: multiplies by 100 (stored as 0–1 fraction)

### Component: `WAExplorerView`

Props: `rows: WAExplorerRow[]`, `config: ConfigResponse`.

Same general table structure as ExplorerView but hierarchy is GWA → IWA → DWA → Tasks.

**Level selector:** GWA / IWA / DWA / Task. Task level uses the same all-eco-tasks dataset as ExplorerView (fetched once from `/api/explorer/all-eco-tasks`).

**Columns:** name, occ, broad_cat, minor_cat, major_cat, dwa_col, iwa_col, gwa_col, emp, wage, n_tasks, pct_phys, auto_avg/max (with_vals/all), pct_avg/max, sum_pct. At task level, "name" is the task text and occ/broad/minor/major/dwa/iwa/gwa columns are populated.

**Column selector (gear icon):**
- Simple mode (non-task level): only `WA_SIMPLE_COLS` are selectable
- Simple mode (task level): only `WA_SIMPLE_TASK_COLS` are selectable
- Advanced mode: all columns selectable; selection persisted to localStorage

**Text column filters (`TextColumnFilterDropdown`):**
- Available for occ, major_cat, minor_cat, broad_cat, dwa_col, iwa_col, gwa_col columns
- Funnel icon in column header opens a multi-select dropdown of all unique values in that column
- Applied to `topRows` after numeric and text filters

**DWA row expansion (accordion):**
- Fetches task list via `/api/explorer/wa/tasks` (cached)
- Renders a `WATaskSubHeader` + `WATaskSubRow` per task (11 columns: Task, Physical, Freq, Imp, Rel, auto_aug, pct_norm, avg_auto_aug, max_auto_aug, pct_aff, workers_aff/wages_aff)
- Each sub-row is itself expandable to show an inline Task Details panel (physical/freq/imp/rel/auto/pct) and a Top MCPs panel (if applicable)
- pct_affected is injected from `pctAffectedMap` — keyed by **DWA activity name** (not task text)

**Task-level expansion:**
- Expands to show Occupation Classification (occ → broad → minor → major), Activity Classification (GWA/IWA/DWA), Task Details panel (physical/freq/imp/rel/auto/pct), and Top MCPs panel
- pct_affected injected via `pctAffectedMap.get(r.dwa_title ?? "")` — uses DWA title as key (not task text)

**`WaPctComputePanel`:** Same as ExplorerView `PctComputePanel` but calls `/api/work-activities` with the current WA settings. Injects pct/workers/wages columns. Dataset selection uses `enforceDatasetToggle` from `lib/datasetRules.ts`.

**Emp weighting toggle:** An "Emp Weight" segmented control (Time / Value) next to other controls. Controls which emp allocation variant is displayed (`emp_nat_freq`/`emp_ut_freq` vs `emp_nat_value`/`emp_ut_value`). Hidden in simple mode (defaults to freq/Time). Affects both activity-level and accordion task sub-rows.

**Section titles in task expansions:** Occupation Categories, Work Activities, Task Detail, Source Breakdown, Top MCP Servers — consistent across both explorers.

**Accordion Task Detail (DWA expansion):** Shows physical, freq, imp, rel, emp, wage, auto avg/max, pct avg/max in a side table.

**Task-level Task Detail:** Shows physical, freq, imp, rel, emp, wage only (no auto/pct — those are already visible as table columns).

**GWA multi-select pills** (always visible, including simple mode), same sort/filter/search/pagination/Avg/Max/Nat/Utah patterns as ExplorerView.

### Utility: `lib/datasetRules.ts`

Shared dataset selection enforcement. Exports:
- `DatasetClassification` interface: `{ aeiSnapshotDatasets, aeiCumulativeDatasets, mcpDatasets }`
- `enforceDatasetToggle(current, name, cls)` — returns the new selection after toggling `name`, with rules applied:
  - Selecting a **cumulative AEI** → removes all other cumulative and all snapshot AEI
  - Selecting a **snapshot AEI** → removes all cumulative AEI
  - Selecting an **MCP** → removes all other MCP (only one MCP at a time)
  - Deselecting anything → always allowed
- `getDatasetConflictMessage(current, cls)` — returns a conflict description string or null if valid

Used by: `ExplorerView` `PctComputePanel`, `WAExplorerView` `WaPctComputePanel`, `occupation-categories/page.tsx` `DatasetPills`, `work-activities/page.tsx` `DatasetPillsWA`.

The classification arrays are sourced from `config.aei_snapshot_datasets`, `config.aei_cumulative_datasets`, `config.mcp_datasets` (from `GET /api/config`).

### Utility: `downloadChart.ts`

`downloadChartAsPng(container, filename, options)`:
1. Clones SVG from container
2. Creates canvas (DPR-adjusted), renders title → chart → legend grid → config footer
3. Legend: `LEGEND_COLS = min(4, floor(width / 210))`; colored circles + truncated labels + extra badges
4. Config footer: small grey text below separator
5. Triggers PNG download

---

## 7. Caching Strategy

All caching is in-module Python dicts. **Nothing invalidates caches except server restart.**

| Cache Variable | Key | What's Cached |
|----------------|-----|---------------|
| `_crosswalk_cache` | singleton | Crosswalk DataFrame |
| `_eco_raw_cache` | singleton | Raw eco_2025 DataFrame |
| `_eco2015_raw_cache` | singleton | Raw eco_2015 DataFrame |
| `_eco_baseline_cache` | `(method, physical_mode, geo)` | Deduped eco with task_comp |
| `_dataset_cache` | `(file_path, is_aei, method, use_auto_aug, use_adj_mean, physical_mode, geo, agg_level)` | Single-dataset compute result |
| `_explorer_occ_cache` | singleton | 923 occupation summaries |
| `_explorer_task_cache` | `title` string | Task details per occupation |
| `_explorer_task_lookup_cache` | singleton | task_normalized → sources lookup |
| `_explorer_groups_cache` | singleton | Major/minor/broad group rows |
| `_wa_explorer_cache` | singleton | WA explorer rows (GWA/IWA/DWA) |
| `_all_tasks_cache` | singleton | All unique tasks with metrics |
| `_all_eco_task_rows_cache` | singleton | All ~23,850 eco_2025 task×occ rows with AI metrics |
| `_top_mcps_cache` | singleton | `task_normalized → [{title, url}]` from MCP v4 top_mcps column |
| `_wa_cache` | (varies) | Work activity computation results |
| `_trends_cache` | (varies) | Trends computation results |

The explorer endpoints are **cold-start heavy** (~2–5s on first `/api/explorer` call) because they precompute all 923 occupations with all 8 sources. Subsequent calls are instant.

---

## 8. Common Pitfalls

1. **Eco 2015 is not user-selectable.** It's only an internal baseline for AEI work-activity analysis.

2. **SOC version mismatch.** AEI uses `title` (2010 SOC); MCP/Microsoft use `title_current` (2019 SOC). Don't mix without crosswalk.

3. **Crosswalk CSV location.** Not in `data/` by default — config searches multiple sibling paths.

4. **`pct_normalized` and `auto_aug_mean` are zero/null in eco files.** Values must come from AI datasets.

5. **`pct_normalized` is already in percent form.** 0.4 means 0.4%, NOT 40%. Do NOT multiply by 100 before display. `fmtPctNorm(v)` uses `v` directly.

6. **Group-level metrics must be computed from unique task_norms**, not averaged from occupation-level values. Averaging sub-group metrics produces incorrect results.

7. **Work Activities: AEI and MCP/Microsoft cannot mix.** They use different ECO baselines (2015 vs 2025). Client-side `isMixed()` check blocks this.

8. **`ComputeResponse.total_emp` and `total_wages` are economy-wide sums** (before top-N filter), used for economy-share % in tooltips.

9. **Trends backend receives family names, not individual datasets.** `getSeriesToFetch()` maps selected individual datasets → families. Frontend filters data_points by individual dataset name.

10. **Trends cumulative max carries forward.** If a category has no data at a date, the running max from prior dates is used — it never decreases.

11. **Explorer child rows use `childRowCache` useMemo Map** (keyed `"level:name"`). Do NOT re-filter arrays inside render functions — use the pre-built cache.

12. **Explorer pagination is 100 rows at a time** for all levels. Never render all rows at once — occupation level has 923+ rows and DWA has hundreds, causing DOM jank with 10K+ nodes.

13. **Search inputs are debounced** (250–300ms via `useDebounce`) before inclusion in `topRows` useMemo deps. Do not use raw input state in useMemo deps.

14. **Filter icon (`FunnelIcon`) in explorer column headers must be `position: absolute`** inside the `<th>`. Placing it inside the inline-flex label div pushes column text and overflows into adjacent columns.

15. **`InfoTooltip` uses `createPortal` into `document.body`** — required to avoid clipping by `overflow: hidden` ancestors. Position is `fixed` at mouse coordinates.

16. **`AllTaskRow.emp_nat/emp_ut/wage_nat` are allocated values** — computed as `Σ(emp_occ / n_unique_tasks_per_occ)` across sharing occupations. Not the same as occupation-level employment totals.

17. **`pct_physical` is stored as a 0–1 fraction.** `fmtPctPhys(v)` multiplies by 100 for display.

18. **`use_adj_mean` only applies to MCP datasets.** Backend applies it as `effective_adj = use_adj_mean and meta["is_mcp"]`.

19. **Overview/WA pages use staged settings.** `pending*` is form state; `fullResponse*` is backend results (topN=1000); `displayResponse*` is client-filtered. Charts only update on "Run" click.

20. **Trends frozen tooltip:** `lockedPos` is screen-space; the fixed `<div>` must be clamped to `window.innerHeight/innerWidth` to stay on-screen. Always shows all lines at the locked date (sorted by value desc, scrollable). A `dotClickedRef` flag prevents the parent div click handler from clearing the lock when clicking a dot.

21. **DWA emp allocation in WA Explorer** deduplicates on `(title_current, task_normalized)` within each activity — not globally. Each activity level (GWA/IWA/DWA) deduplicates independently.

22. **All 8 sources are shown in explorer task breakdowns** (AEI v1–v4, AEI API v3–v4, MCP v4, Microsoft) — not just latest versions.

23. **Explorer `PctComputePanel`** calls `/api/compute` with `aggLevel: "occupation"`, `topN: 1000`. Physical filter affects numerator only, consistent with the rest of the app.

24. **Currency formatting is adaptive.** `fmtChartValue` (HorizontalBarChart) and `fmtVal` (TrendsView) display wages in billions ($B) when ≥ $1B, millions ($M) when ≥ $1M, thousands ($K) when ≥ $1K, otherwise raw dollars. TrendsView values are already divided by 1e9 before reaching `fmtVal`, so thresholds are 1 / 0.001 / 0.000001. Explorer `wages_aff` cells use the same adaptive logic.

25. **Simple mode auto-computes explorer pct.** In simple mode, `ExplorerView` and `WAExplorerView` run a `useEffect` that calls `fetchCompute` / `fetchWorkActivities` with preset settings (all datasets / all AEI, freq, all phys, auto-aug on) on mount and when `geo` / `tableLevel` changes. The `PctComputePanel` UI is hidden.

26. **`pctAffectedMap` in WAExplorerView is keyed by DWA activity name, not task text.** At the DWA level the map key is `r.name` (the DWA name). At the Task level each row's `r.name` is the task text — use `r.dwa_title ?? ""` as the lookup key to find the parent DWA's pct_affected. Using `r.name` at task level produces no matches.

27. **Dataset selection enforcement is client-side only.** `enforceDatasetToggle()` in `lib/datasetRules.ts` auto-deselects conflicting datasets in the UI. The backend does not enforce these rules — any combination technically computes, but the results are only meaningful when selection constraints are respected (e.g., cumulative AEI v4 already includes v1–v3, so selecting multiple cumulative versions is redundant).

28. **Cumulative AEI datasets cannot be mixed with snapshot AEI datasets.** `AEI Cumul. v1–v4` and `AEI v1–v4 / AEI API v3–v4` are mutually exclusive. The cumulative versions aggregate all conversations up to their snapshot date, so their scale is not comparable to the per-snapshot versions.

29. **WA emp allocation is method-weighted, not equal-split.** The backend returns both freq-weighted and value-weighted emp variants for WA explorer rows and WA task details. The frontend emp weighting toggle selects which variant to display. The WA charts page's Time/Value method toggle controls both task_comp AND emp weighting simultaneously.

30. **PctComputePanel auto-recomputes on geo change.** Both `PctComputePanel` (occ explorer) and `WaPctComputePanel` (WA explorer) track `geo` changes via a ref and auto-recompute when the panel has already been computed and the geo changes. Simple mode auto-compute already handles this via its useEffect dependency on `geo`.
