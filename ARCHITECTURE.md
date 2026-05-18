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
├── analysis/            — Research analysis system (see analysis/ANALYSIS.md)
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
| AEI Conv. v1–v5 | `final_aei_v{1..5}.csv` | 2010 | true | false | Snapshot; needs crosswalk to 2019 |
| AEI API v3–v5 | `final_aei_api_v{3..5}.csv` | 2010 | true | false | Snapshot; needs crosswalk to 2019 |
| AEI Cumul. Conv. v1/v2 | `final_aei_cumulative_v{1,2}.csv` | 2010 | true | false | Cumulative (each version accumulates all prior); needs crosswalk. |
| AEI Cumul. Conv. v3–v5 | `final_aei_cumulative_aei_only_v{3..5}.csv` | 2010 | true | false | Cumulative AEI-only conv.; needs crosswalk. |
| AEI Cumul. (Both) v3–v5 | `final_aei_cumulative_v{3..5}.csv` | 2010 | true | false | Cumulative (AEI + API combined); needs crosswalk. |
| AEI API Cumul. v4–v5 | `final_aei_cumulative_api_only_v{4,5}.csv` | 2010 | true | false | Cumulative API-only; needs crosswalk. |
| MCP Cumul. v1–v4 | `final_mcp_v{1..4}.csv` | 2019 | false | true | Only one version at a time |
| Microsoft | `final_microsoft.csv` | 2019 | false | false | Single snapshot |

**Dataset families in `config.py`:**
- `AEI_CONV_SNAPSHOT_DATASETS` — `{"AEI Conv. v1", ..., "AEI Conv. v5"}`
- `AEI_API_SNAPSHOT_DATASETS` — `{"AEI API v3", "AEI API v4", "AEI API v5"}`
- `AEI_CONV_CUMULATIVE_DATASETS` — `{"AEI Cumul. Conv. v1", ..., "AEI Cumul. Conv. v5"}`
- `AEI_API_CUMULATIVE_DATASETS` — `{"AEI API Cumul. v4", "AEI API Cumul. v5"}`
- `AEI_BOTH_CUMULATIVE_DATASETS` — `{"AEI Cumul. (Both) v3", "AEI Cumul. (Both) v4", "AEI Cumul. (Both) v5"}`
- `MCP_DATASETS` — `{"MCP Cumul. v1", ..., "MCP Cumul. v4"}`

Total selectable datasets: 26.

These sets are exposed via `GET /api/config` as `aei_conv_snapshot_datasets`, `aei_api_snapshot_datasets`, `aei_conv_cumulative_datasets`, `aei_api_cumulative_datasets`, `aei_both_cumulative_datasets`, `mcp_datasets` and consumed by `frontend/src/lib/datasetRules.ts` for selection enforcement (see §6).

### Baseline Files (not user-selectable)

| File | Purpose |
|------|---------|
| `final_eco_2025.csv` (~23,850 rows) | Primary ECO baseline (denominator for all metrics). Has `task_prop`, `title_current` (2019 SOC). |
| `final_eco_2015.csv` (~24,631 rows) | AEI work-activity baseline. Has `title` (2010 SOC). |
| `2010_to_2019_soc_crosswalk.csv` | Maps 2010 SOC → 2019 SOC. Searched in `data/`, then `../aea_dashboard_dev/data/`, then `../automation_exposure_analysis/data/`. |
| `mcp_titles_desc.csv` | Per-MCP-server descriptions (`title`, `text_for_llm`). Used by `/api/occupation-report` to enrich the top-5 MCP servers shown for each task. |

### Static Reference Files (from `analysis/data/`, used by `occupation_report.py`)

These live in `analysis/data/` rather than `data/` for historical reasons (the analysis bucket loaded them first), but the Dockerfile explicitly copies them into the production image so the backend can read them at runtime. They have no Python deps — pure CSV reference data.

| File | Purpose |
|------|---------|
| `skills_v30.1.csv` / `abilities_v30.1.csv` / `knowledge_v30.1.csv` | O*NET v30.1 SKA element scores (importance + level per occupation). Required for the SKA gap section and similarity matrix. |
| `tech_skills_simple.csv` | Per-occupation `n_software` count. Required for risk-score flag 7. |
| `technology_skills_v30.1.csv` | One row per (occupation, specific software) entry, with commodity category. Required for the tech-tools section. |

### Shared Columns Across All Datasets

| Column | Type | Description |
|--------|------|-------------|
| `task`, `task_normalized` | str | O*NET task text (raw and normalized) |
| `dwa_title`, `iwa_title`, `gwa_title` | str | O*NET work activity hierarchy |
| `freq_mean` | 0–10 | Task frequency (O*NET survey) |
| `importance` | 0–5 | Task importance (O*NET survey) |
| `relevance` | 0–100 | Task relevance (O*NET survey) |
| `auto_aug_mean` | 0–5 | AI automatability score |
| `pct_normalized` | float | Share of AI conversations involving this task. **Already in percent form** (0.4 = 0.4%, NOT 40%) |
| `physical` | bool | Truly physical task |
| `date` | str | Dataset snapshot date |
| `emp_tot_{geo}_2025` | float | BLS OEWS 2025 employment per geography (nat, al, ak, ..., wy, gu, pr, vi) |
| `a_med_{geo}_2025` | float | BLS OEWS 2025 median annual wage per geography |
| `dws_star_rating` | 1–5 | ECO 2025 only — DWS job outlook star rating |
| `job_zone` | 1–5 | ECO 2025 only — O*NET job zone |
| `task_prop` | float | ECO 2025 only — ratio of 2025/2015 tasks per occupation |
| `soc_code_2010` | str | AEI datasets only — used for crosswalk |

### Dataset Dates (for Trends)

| Dataset | Date |
|---------|------|
| AEI Conv. v1 | 2024-12-23 |
| AEI Conv. v2 | 2025-03-06 |
| AEI Conv. v3 | 2025-08-11 |
| AEI Conv. v4 | 2025-11-13 |
| AEI API v3 | 2025-08-11 |
| AEI API v4 | 2025-11-13 |
| AEI Cumul. Conv. v1 | 2024-12-23 |
| AEI Cumul. Conv. v2 | 2025-03-06 |
| AEI Cumul. Conv. v3 | 2025-08-11 |
| AEI Cumul. Conv. v4 | 2025-11-13 |
| AEI Cumul. (Both) v3 | 2025-08-11 |
| AEI Cumul. (Both) v4 | 2025-11-13 |
| AEI Conv. v5 | 2026-02-12 |
| AEI API v5 | 2026-02-12 |
| AEI Cumul. Conv. v5 | 2026-02-12 |
| AEI Cumul. (Both) v5 | 2026-02-12 |
| AEI API Cumul. v4 | 2025-11-13 |
| AEI API Cumul. v5 | 2026-02-12 |
| MCP Cumul. v1 | 2025-04-24 |
| MCP Cumul. v2 | 2025-05-24 |
| MCP Cumul. v3 | 2025-07-23 |
| MCP Cumul. v4 | 2026-02-18 |
| Microsoft | 2024-09-30 |

**ECO 2015 note:** `auto_aug_mean` and `pct_normalized` are all null/zero in eco files — values must come from AI datasets.

---

## 3. Backend Module Structure

### `config.py` — Registry & Constants

```python
DATASETS           # dict[str, {file, is_aei, is_mcp}] — 26 selectable datasets
ECO_2015_META      # internal-only baseline for AEI work-activity analysis
AEI_CONV_SNAPSHOT_DATASETS    # set of snapshot AEI conv. names: {AEI Conv. v1..v5}
AEI_API_SNAPSHOT_DATASETS     # set of snapshot AEI API names: {AEI API v3..v5}
AEI_CONV_CUMULATIVE_DATASETS  # set of cumulative AEI conv. names: {AEI Cumul. Conv. v1..v5}
AEI_API_CUMULATIVE_DATASETS   # set of cumulative AEI API names: {AEI API Cumul. v4, v5}
AEI_BOTH_CUMULATIVE_DATASETS  # set of cumulative AEI both names: {AEI Cumul. (Both) v3..v5}
MCP_DATASETS       # set of MCP names: {MCP Cumul. v1..v4}
DATASET_SERIES     # {"AEI Conv.": ["AEI Conv. v1"..v5], ...}
GEO_OPTIONS        # dict[str, str] — geo code → display name (55 entries: nat + 50 states + DC + 3 territories)
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
- `compute_task_comp(df, method, use_auto_aug)` → `pd.Series` of task completion weights
- `dedup_and_compute(df, title_col, emp_col, wage_col, method, ...)` — deduplicates on `(title, task_normalized)`, computes `task_comp`

#### Stage 3: ECO Baseline
- `load_eco_baseline(method, physical_mode, geo)` — deduped eco_2025 with task_comp computed (no auto_aug). Cached by `(method, physical_mode, geo)`.

#### Stage 4: Single-Dataset Compute
- `compute_single_dataset(file_path, is_aei, method, use_auto_aug, physical_mode, geo, agg_level)` — full pipeline for one AI dataset. If AEI: runs crosswalk pipeline (§4.3). If MCP/MS: dedup + compute directly. Calls `aggregate_results()` at the end. Cached by full parameter tuple.

#### Stage 5: Aggregation
- `aggregate_results(ai_df, eco_df, title_col, agg_level, emp_col, wage_col)` — computes pct/workers/wages at occupation level, then rolls up to requested agg_level. Also computes rank columns.

#### Stage 6: Multi-Dataset Combination
- `combine_results(results, group_col, combine_method)` — outer-joins multiple DataFrames, applies Average or Max per metric column.

#### Stage 7: Orchestration
- `get_group_data(settings)` — orchestrates the full pipeline for one sidebar group. Returns top-N or search-windowed rows plus `total_categories`, `total_emp`, `total_wages`, `matched_category`.
- `compute_work_activities(settings)` — splits datasets into AEI group (eco_2015 baseline) and MCP/MS group (eco_2025 baseline). Calls `_compute_wa_for_group()` for each.
- `compute_trends(settings)` — for each sub_type series key, looks up datasets from `DATASET_SERIES`, runs `compute_single_dataset` for every version, records date, returns time series.
- `compute_wa_trends(settings)` — same but for work activities, using `_compute_wa_for_group()` per dataset version. Series names are sub_type keys from `DATASET_SERIES`. AEI sub_types (keys starting with "AEI") use eco_2015 baseline; others use eco_2025.

#### Stage 8: Explorer
- `get_explorer_source_names()` — returns the list of source names used in the explorer task lookup: `AEI_EXPLORER_DATASETS + ["MCP", "Microsoft"]`. Exposed via `/api/config` as `explorer_source_names`.
- `_build_explorer_task_lookup()` — builds `task_normalized → {source_name: {auto_aug, pct_norm}}` across all 8+ sources. AEI values averaged across 2010 SOC titles. Cached.
- `_compute_task_metrics(task_norms, lookup, selected_sources=None)` — given task list + lookup, returns 10 metric fields (§4.6). When `selected_sources` (a frozenset of source names) is provided, only those sources contribute to metrics. When None, all sources are used.
- `_build_explorer_occ_base(selected_sources=None)` — builds geo-independent base for occupations (hierarchy, dws, job_zone, task counts, metrics). Cached in `_explorer_occ_base_cache` keyed by `frozenset|None`.
- `get_explorer_occupations(geo="nat", selected_sources=None)` — 923 occupation summaries with hierarchy, single `emp`/`wage` for requested geo, 10 metrics. Base cached; emp/wage overlaid per geo. `selected_sources` filters which AI datasets contribute to metrics.
- `_build_explorer_groups_base(selected_sources=None)` — builds geo-independent base for groups (hierarchy, metrics, parent info, dws, job_zone, task counts, `_occs` set). Cached in `_explorer_groups_base_cache` keyed by `frozenset|None`.
- `get_explorer_groups(geo="nat", selected_sources=None)` — pre-computed major/minor/broad aggregations (unique task_norms per group, not averages of occ-level values). Single `emp`/`wage` per geo. Base cached; emp/wage overlaid per geo. `selected_sources` filters which AI datasets contribute to metrics.
- `get_occupation_tasks(title)` — task details for one occupation (all 8 sources). Cached per title.
- `get_all_tasks(geo="nat")` — all unique tasks (deduplicated by `task_normalized`) with metrics + allocated `emp`/`wage` for requested geo. Cached per geo in `_all_tasks_geo_cache`.
- `get_all_eco_task_rows(geo="nat", selected_sources=None)` — all ~23,850 rows from eco_2025 (each task x occupation combination) with occupation hierarchy, raw `emp`/`wage`, weighted emp allocation fields (`emp_freq`, `emp_value`), and AI metrics from the task lookup. Cached per `(geo, selected_sources)` in `_all_eco_tasks_geo_cache`. Used by both explorer task-level views. `selected_sources` filters which AI datasets contribute to metrics.
- `get_wa_explorer_data(geo="nat", selected_sources=None)` — GWA/IWA/DWA rows with emp allocation (`emp_freq`/`emp_value`/`wage_freq`/`wage_value`) + metrics. Cached per `(geo, selected_sources)` in `_wa_explorer_geo_cache`. `selected_sources` filters which AI datasets contribute to metrics.
- `get_wa_tasks_for_activity(level, name, geo="nat")` — task details for one WA activity. Cached per `(level, name, geo)` in `_wa_cache`.

#### Stage 9: Task Changes
- `_build_eco2015_baseline_set()` — builds set of (task_normalized, title_current) from crosswalked eco_2015. Cached.
- `_prepare_dataset_for_comparison(ds_name)` — loads a dataset, crosswalks AEI to 2019 SOC, deduplicates to (task_normalized, title_current) level with averaged auto_aug_mean and pct_normalized. Returns DataFrame.
- `compute_task_changes(from_dataset, to_dataset, geo="nat")` — compares two datasets at task level. Returns list of dicts with status, deltas, `emp`/`wage` for requested geo, and metadata. Cached by (from_dataset, to_dataset, geo).

### `occupation_report.py` — Per-Occupation Report

Composes one big payload for the `/my-occupation` page. Lives outside `compute.py` because (a) it only ever runs at occupation level, (b) it pulls in static O*NET reference data (skills/abilities/knowledge + tech skills CSVs from `analysis/data/`), and (c) it inlines small portions of analysis-folder logic — SKA computation and equal-consensus bias ratios — to keep the backend self-contained for production deployment (analysis/ is not in the Docker image except for the static reference CSVs explicitly copied via the Dockerfile).

**Primary dataset:** all headline metrics, the SKA gap reference, the risk score, the trend sparkline, the intensity rank, and the tech commodity ranking are computed against `AEI Both + Micro 2026-02-12`. Per-task auto_aug per source comes from `_build_explorer_task_lookup()` (same pipeline the Occupation Explorer uses).

**Section builders (all called by `get_occupation_report()`):**
- `_build_headline(title, geo)` — title, hierarchy, job zone, outlook, n_tasks, raw emp/wage from `_raw_emp_wage()` (eco_2025 BLS columns), pct/workers/wages from `_emp_wage_for(PRIMARY_DATASET, geo)`, risk payload from `_risk_table()`, intensity from `_intensity_rank_table()`.
- `_build_tasks(title)` — all unique tasks for this occ from eco_2025; per-task max across `AEI Conv. v1–v5`, max across `AEI API v3–v5`, plus single Microsoft and MCP scores, color bucket from max(AEI Conv max, AEI API max, MS), top-5 MCPs enriched with `text_for_llm` descriptions from `data/mcp_titles_desc.csv`. Sorted by color_driver desc.
- `_build_was(tasks, geo)` — rolls the task list up to GWA/IWA/DWA. Per-WA values are simple averages of the per-task scores within each WA. Each WA row also gets an `eco_stats` block from `_eco_wa_stats(geo)` — economy-wide pct/workers/wages/auto_aug for that WA plus rank within all WAs at that level.
- `_eco_wa_stats(geo)` — for each level (gwa/iwa/dwa), runs `compute_work_activities()` on the primary dataset to get per-WA pct/workers/wages, joins per-WA `auto_aug_mean` from a one-pass groupby on the dataset CSV, and computes 1-indexed ranks per metric across all WAs at that level. Cached per geo. Used by `_build_was`.
- `_build_group_ranks(title, geo)` — rank in economy / major / minor / broad on pct_tasks_affected, workers_affected, wages_affected. Built by sorting all 923 occs from `_emp_wage_for(PRIMARY_DATASET, geo)`.
- `_build_trend(title, geo)` — pct_tasks_affected at each of the four `all_confirmed` snapshot dates (Mar 2025 → Feb 2026).
- `_build_ska(title)` — per-element rows (Skills/Abilities/Knowledge separate, importance ≥ 3 only) using `_compute_ska_for_pct(pct)` and `_ska_top10_per_element()`. Per row: importance, level, occ_score (imp × lv), ai_top10 reference (mean of top-10 ai_product values for that element across all occs), gap (ai_top10 − occ_score), pct_of_need, color bucket. Sorted with biggest AI lead at top within each section.
- `_build_sector_stats(title, geo)` — major-category aggregate stats. Thin wrapper over `_sector_stats_at_level(title, "major", geo)` kept for backwards compatibility with the legacy `sector` payload key.
- `_ranked_group_df(level, geo)` / `_sector_stats_at_level(title, level, geo)` — generic per-SOC-level (`major`/`minor`/`broad`) ranked group dataframe via `get_group_data()` for the primary dataset, returning the occ's row plus rank columns and the level's total. Cached per `(level, geo)`.
- `_build_sector_chain(title, geo)` — runs `_sector_stats_at_level` at `major`, `minor`, and `broad` and returns all three. Powers the new `sector_chain` payload key.
- `_similar_occs(title, n)` — L1 distance over the `_ska_profile_matrix()` (one row per occ, one column per (type, element_name) with imp ≥ 3 in any occ; cell = importance × level or 0). Returns the n smallest distances excluding self, with each occ's pct, wage, job zone, outlook, plus its `risk` block (score / tier / 8 flags) so the UI can render an exposure profile column on the Similar table.
- `_tech_for_occ(title)` — softwares from O*NET `technology_skills_v30.1.csv` for this occupation, joined with `_tech_commodity_rank()` (every commodity's economy-wide rank by avg pct_tasks_affected).

**Risk table (`_risk_table()`):** mirrors the canonical 8-flag risk score (originally from `analysis/_archive/questions/job_exposure/job_risk_scoring/run.py`; spec now lives in `analysis/ANALYSIS_ARCHITECTURE.md` § Risk Scoring Flags). 8 binary flags weighted 1× or 2× (max 10), exposure gate at pct < 33% downgrades score-8+ to mod_high. Uses pct_first/pct_last from `TREND_SERIES` for the trend flags, SKA overall_pct for flag 2, `n_software` from `analysis/data/tech_skills_simple.csv` for flag 7, `auto_avg_with_vals` from the explorer for flag 8. Cached once.

**Intensity rank (`_intensity_rank_table()`):** mirrors `analysis/exploratory/audit_pct_norm_eco/run_v2.compute_intensity_metric` for `equal` consensus + `configscoped` eco + no smoothing, computed for both occupation and major levels. Bias ratios inlined as `_equal_consensus_bias_ratios()` from the Claude/Copilot/ChatGPT GWA share constants. Returns each occ's `ratio_pct` (renormalized to sum to 100 across cats) and rank within its level.

**Caches** (all module-level, lazy):
- `_pct_by_dataset_cache` — keyed by `f"{dataset}|{geo}"`, holds pct Series.
- `_ska_data_cache`, `_ska_result_cache`, `_ska_top10_per_element_cache`, `_ska_profile_matrix_cache` — SKA pipeline.
- `_intensity_rank_cache`, `_risk_table_cache`, `_tech_commodity_rank_cache` — cross-occ precomputes.
- `_mcp_titles_desc_cache`, `_explorer_occ_index_cache` — per-payload helpers.
- `_eco_wa_stats_cache` — per-geo dict of economy-wide WA stats (pct/workers/wages/auto + ranks) at gwa/iwa/dwa.
- `_sector_level_cache` — per-`(level, geo)` ranked group dataframe used to look up sector_chain stats at major/minor/broad.

**Public entrypoints:**
- `get_occupation_titles() -> list[str]` — sorted list of 923 titles.
- `get_occupation_report(title, geo="nat") -> dict | None` — full payload; None if title not in eco_2025.

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

The backend computes BOTH freq and value weightings simultaneously for the WA explorer endpoints, returning dual field sets (`emp_freq`, `emp_value`, `wage_freq`, `wage_value`) for the requested geography so the frontend can toggle without re-fetching.

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
- **AEI Conv. v1–v4 + AEI API v3–v4**: groups by `task_normalized`, takes mean of `auto_aug_mean` and `pct_normalized` across all 2010 SOC titles sharing that task
- **MCP Cumul. v4**: uses `auto_aug_mean`
- **Microsoft**: uses `auto_aug_mean`

Result: `dict[task_normalized → dict[source_name → {auto_aug: float|None, pct_norm: float|None}]]`

### 4.8 Explorer Emp/Wage Allocation (All Tasks)

For the Task-level flat table (`get_all_tasks()`):
```
n_unique_tasks_per_occ = count of unique task_norms in that occ (from eco_2025)
emp_contrib_per_task   = emp_occ / n_unique_tasks_per_occ

emp for a task = Σ(emp_contrib_per_task) across all occupations sharing that task
wage           = employment-weighted median: Σ(emp_contrib × wage) / Σ(emp_contrib)
```

Same allocation logic used for WA Explorer rows.

### 4.8.1 All Eco Task Rows (`get_all_eco_task_rows()`)

For the Task-level view in both explorers, returns every row from eco_2025 (~23,850 rows) as a task × occupation combination. Each row includes:
- `task`, `task_normalized` — task text (properly cased) and dedup key
- `title_current`, `broad_occ`, `minor_occ_category`, `major_occ_category` — occupation hierarchy
- `dwa_title`, `iwa_title`, `gwa_title` — work activity hierarchy
- `physical` — physical task flag
- `emp`, `wage` — **raw** occupation-level BLS numbers for the requested geography (NOT divided by task count)
- `emp_freq`, `emp_value` — weighted emp allocation per task x occ for the requested geography (freq-weighted and value-weighted, same logic as WA explorer emp allocation)
- `freq_mean`, `importance`, `relevance` — O*NET survey measures read directly from eco_2025 rows
- `sources`, `avg_auto_aug`, `max_auto_aug`, `avg_pct_norm`, `max_pct_norm` — AI metrics from the task lookup

Weighted emp allocation uses the same approach as WA explorer (§4.5): for each occupation, tasks are deduplicated on `(title_current, task_normalized)`, freq and value weights are computed per task, and each task receives `(weight / Σweight_per_occ) × emp_occ`. Both freq and value variants are pre-computed so the frontend can switch without re-fetching. The WA Explorer task view selects the appropriate variant based on the Time/Value toggle.

### 4.9 Trends

`compute_trends()` iterates over each sub_type series key (e.g., "AEI Both + Micro", "MCP"), looks up datasets from `DATASET_SERIES`, runs `compute_single_dataset()` for each version, and records the date (read from the CSV's `date` column). Returns all rows (not just top-N) per data point so the frontend can filter.

`compute_wa_trends()` works similarly but uses `_compute_wa_for_group()` per dataset version. AEI sub_types (keys starting with "AEI") use eco_2015 baseline; others use eco_2025.

`top_categories` is set from the last (most recent) dataset version — these are the reference categories for the series.

**Frontend date-range filtering:** The user selects a date range (from/to) and sub_types. The backend receives sub_type keys as `series`, computes all versions in those sub_types, but the frontend resolves sub_type + date range → dataset names via `getDatasetsInRange()` and filters `data_points` by `dp.dataset` before building chart data. This allows the full backend response to be cached while the frontend adjusts the visible date range without refetching.

**Cumulative max mode** (frontend): value at date T = max of all dataset values at dates ≤ T, tracked via a running-max Map that carries forward. The line never decreases.

### 4.10 Multi-Dataset Combination

`combine_results()` (occupation-level) and `_combine_activity_dfs()` (activity-level):

1. Rename metric columns with `_0`, `_1`, etc. suffixes
2. Outer-join all DataFrames on the group column
3. For each metric: take `max(axis=1)` or `mean(axis=1)` across the suffixed columns

### 4.11 Search / Context Window

Backend sorts all categories descending by the selected metric, finds the first case-insensitive `contains` match, slices `[idx - contextSize : idx + contextSize + 1]`, and returns `matched_category` in the response. The matched bar is highlighted orange in the chart.

### 4.12 Task Changes Comparison

Compares two datasets at the task level to identify what changed between versions.

**Pipeline:**
1. Load both datasets via `_prepare_dataset_for_comparison()` — crosswalks AEI to 2019 SOC, groups by (task_normalized, title_current), averages auto_aug_mean and pct_normalized
2. Full outer join on (task_normalized, title_current)
3. Build eco baseline sets: eco_2025 set for MCP/Microsoft, crosswalked eco_2015 set for AEI
4. Assign status per row:
   - **New** — in "to" only, and (task, occ) exists in "from" dataset's eco baseline
   - **Removed** — in "from" only, and (task, occ) exists in "to" dataset's eco baseline
   - **Changed** — in both, auto_aug scores differ (including null-vs-value)
   - **Unchanged** — in both, same auto_aug scores
   - **Not in baseline** — task-occ pair doesn't exist in the other dataset's eco baseline (cross-family only)
5. Enrich with eco_2025 metadata (occupation hierarchy, work activities, emp, wage, physical)
6. Attach source breakdown and top MCPs from explorer task lookup

---

## 5. API Contracts

### `GET /api/health`
Returns `{"status": "ok"}`.

### `GET /api/config`

Response:
```ts
{
  datasets: string[];                        // all dataset names (21 selectable)
  dataset_availability: Record<string, boolean>;
  dataset_series: Record<string, string[]>;  // {"AEI Conv.": ["AEI Conv. v1"..], "AEI Cumul. Conv.": [...], "AEI Cumul. (Both)": [...], "AEI API Cumul.": [...], "MCP Cumul.": [...], ...}
  agg_levels: Record<string, string>;        // {"Major Category": "major", ...}
  sort_options: string[];                    // ["Workers Affected", ...]
  crosswalk_available: boolean;
  eco2015_available: boolean;
  aei_conv_snapshot_datasets: string[];     // names of snapshot AEI conv. datasets
  aei_api_snapshot_datasets: string[];      // names of snapshot AEI API datasets
  aei_conv_cumulative_datasets: string[];   // names of cumulative AEI conv. datasets
  aei_api_cumulative_datasets: string[];    // names of cumulative AEI API datasets
  aei_both_cumulative_datasets: string[];   // names of cumulative AEI (both) datasets
  mcp_datasets: string[];                   // names of all MCP datasets
  explorer_source_names: string[];         // AI source names available for explorer metric filtering (e.g. ["AEI Conv. v1", ..., "MCP", "Microsoft"])
}
```

### `POST /api/compute`

Request body (`GroupSettingsModel`):
```ts
{
  selected_datasets: string[];        // e.g., ["AEI Conv. v4", "MCP Cumul. v4"]
  combine_method: string;             // "Average" | "Max"
  method: string;                     // "freq" | "imp"
  use_auto_aug: boolean;
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
  series: string[];                   // sub_type keys, e.g. ["AEI Both + Micro", "MCP"]
  method: string;
  use_auto_aug: boolean;
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
    name: string;                     // sub_type key (e.g., "AEI Both + Micro")
    data_points: Array<{
      dataset: string;                // individual dataset (e.g., "AEI Both + Micro 2025-03-06")
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
  physical_mode: string;
  geo: string;
  top_n: number;
  sort_by: string;
  activity_level: string;             // "gwa" | "iwa" | "dwa"
}
```

Response: same `TrendsResponse` shape as `/api/trends`.

### `GET /api/explorer`

Query params:
- `geo` (string, default `"nat"`) — 2-letter geography code.
- `selected_sources` (string, optional) — comma-separated list of AI source names to include in metric calculations. When omitted or empty, all sources are used. Example: `selected_sources=AEI+Conv.+v5,MCP,Microsoft`.

Response:
```ts
{
  occupations: Array<{
    title_current: string;
    major?: string;
    minor?: string;
    broad?: string;
    emp?: number;
    wage?: number;
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
    dws_star_rating?: number;         // 1–5 DWS star rating (raw for occs)
    job_zone?: number;                // 1–5 O*NET job zone (raw for occs)
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

Query params:
- `geo` (string, default `"nat"`) — 2-letter geography code.
- `selected_sources` (string, optional) — comma-separated list of AI source names (same as `/api/explorer`).

Response:
```ts
{
  major: ExplorerGroupRow[];
  minor: ExplorerGroupRow[];
  broad: ExplorerGroupRow[];
}
// ExplorerGroupRow = { name, parent?, grandparent?, emp, wage, n_occs, n_tasks,
//                      n_physical_tasks, pct_physical, dws_star_rating?, job_zone?, ...10 metric fields }
```

### `GET /api/explorer/all-tasks`

Query params: `geo` (string, default `"nat"`) — 2-letter geography code.

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
    emp?: number;                     // allocated: Σ(emp_occ / n_unique_tasks) across sharing occs
    wage?: number;                    // employment-weighted median
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
  }>;
}
```

### `GET /api/explorer/all-eco-tasks`

Query params:
- `geo` (string, default `"nat"`) — 2-letter geography code.
- `selected_sources` (string, optional) — comma-separated list of AI source names (same as `/api/explorer`).

Returns all ~23,850 eco_2025 rows (one per task x occupation). Used by both explorer task-level views.

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
    emp?: number;                      // raw occupation emp for requested geo (NOT divided)
    wage?: number;                     // raw occupation wage for requested geo (NOT divided)
    emp_freq?: number;                 // freq-weighted emp allocation for this task x occ
    emp_value?: number;                // value-weighted emp allocation (freq x rel x imp)
    freq_mean?: number;                // O*NET task frequency (0-10)
    importance?: number;               // O*NET task importance (0-5)
    relevance?: number;                // O*NET task relevance (0-100)
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
  }>;
}
```

### `GET /api/explorer/wa`

Query params:
- `geo` (string, default `"nat"`) — 2-letter geography code.
- `selected_sources` (string, optional) — comma-separated list of AI source names (same as `/api/explorer`).

Response:
```ts
{
  rows: Array<{
    level: "gwa" | "iwa" | "dwa";
    name: string;
    parent?: string;
    gwa?: string;
    emp_freq?: number;                // freq-weighted emp allocation for requested geo
    emp_value?: number;               // value-weighted emp allocation (freq x rel x imp)
    wage_freq?: number;               // emp-weighted median wage (freq weighting)
    wage_value?: number;              // emp-weighted median wage (value weighting)
    n_occs: number;
    n_tasks: number;
    n_physical_tasks: number;
    pct_physical?: number;
    ...10 metric fields
  }>;
}
```

### `GET /api/explorer/wa/tasks?level=...&name=...&geo=...`

Query params: `level`, `name`, `geo` (string, default `"nat"`) — 2-letter geography code.

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
    emp_freq?: number;                // freq-weighted emp allocation for requested geo
    emp_value?: number;               // value-weighted emp allocation
    wage_freq?: number;               // emp-weighted median wage (freq weighting)
    wage_value?: number;              // emp-weighted median wage (value weighting)
    freq_mean?: number;               // O*NET task frequency (0-10)
    importance?: number;              // O*NET task importance (0-5)
    relevance?: number;               // O*NET task relevance (0-100)
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

### `POST /api/task-changes`

Request body (`TaskChangesRequest`):
```ts
{
  from_dataset: string;   // e.g., "AEI Cumul. Conv. v1"
  to_dataset:   string;   // e.g., "AEI Cumul. Conv. v4"
  geo?:         string;   // 2-letter geography code, default "nat"
}
```

Response (`TaskChangesResponse`):
```ts
{
  rows: Array<{
    task: string;
    task_normalized: string;
    title_current: string;
    broad_occ?: string;
    minor_occ_category?: string;
    major_occ_category?: string;
    dwa_title?: string;
    iwa_title?: string;
    gwa_title?: string;
    physical?: boolean;
    freq_mean?: number;
    importance?: number;
    relevance?: number;
    emp?: number;
    wage?: number;
    status: "new" | "removed" | "changed" | "unchanged" | "not_in_baseline";
    from_auto_aug?: number;
    to_auto_aug?: number;
    delta_auto_aug?: number;
    from_pct?: number;
    to_pct?: number;
    delta_pct?: number;
    sources: Record<string, { auto_aug?: number; pct_norm?: number }>;
    avg_auto_aug?: number;
    max_auto_aug?: number;
    avg_pct_norm?: number;
    max_pct_norm?: number;
    top_mcps: Array<{ title: string; rating?: number; url?: string }>;
  }>;
  from_dataset: string;
  to_dataset: string;
}
```

### `GET /api/occupation-report/titles`

Response:
```ts
{ titles: string[] }   // sorted list of all 923 occupation titles
```

### `GET /api/occupation-report`

Query params:
- `title` (string, required) — full `title_current` from eco_2025.
- `geo` (string, default `"nat"`) — geography code.

Response: full report payload built by `occupation_report.get_occupation_report()`. Top-level keys: `title`, `geo`, `primary_dataset`, `headline`, `tasks`, `work_activities`, `group_ranks`, `trend`, `ska`, `sector`, `sector_chain`, `similar`, `tech`. Each WA row inside `work_activities.{gwa,iwa,dwa}` carries an optional `eco_stats` block with economy-wide pct/workers/wages/auto + per-metric ranks. `sector_chain` exposes major/minor/broad sector aggregates with the same shape as `sector` (pct/workers/wages/3 ranks) so the UI can render the full SOC hierarchy, not just the major. Each entry in `similar` carries an optional `risk` block (score / tier / 8 flags) so the Similar Occupations table can render an exposure-profile chip + flag dots per row. See `frontend/src/lib/types.ts → OccupationReport` for the full TypeScript shape (matches the Python compute output exactly).

Returns 404 if the title isn't in eco_2025; 400 if `geo` is unknown.

---

## 6. Frontend Architecture

### Navigation & Layout

`Navigation.tsx` — fixed 56px nav bar (`var(--nav-height)`), 9 links across 5 groups: My Occupation | Occupation Explorer, Work Activities Explorer | Occupation Categories, Work Activities | Trends, Task Changes Explorer | Instructions, About. Active tab highlighted with brand color. Includes a **Simple/Advanced toggle** button (right side of nav). All pages render below with `paddingTop: var(--nav-height)`.

`Footer.tsx` — global footer displayed below all page content. Contains source attribution text and labeled links: Dashboard GitHub, MCP Classification GitHub, Data Merging GitHub (placeholder — repo not yet available), Research Paper (placeholder — not yet available), and a contact email link.

Root URL (`/`) redirects to `/my-occupation` (Occupation Report is the default landing page).

`layout.tsx` — root layout mounting `<SimpleModeProvider>` → `<Navigation />` + `{children}` + `<Footer />`.

### Simple/Advanced Mode (`lib/SimpleModeContext.tsx`)

React context + provider with localStorage persistence (key: `aea_simple_mode`). Exposes `{ isSimple: boolean, toggle: () => void }` via `useSimpleMode()` hook.

**Hydration safety:** initial render always uses `isSimple = false`; stored value loads on mount to avoid SSR mismatch.

Each page imports `useSimpleMode()` and conditionally:
- Hides/shows controls based on `isSimple`
- Overrides computation settings (datasets, method, physical, auto-aug) at run time
- Explorer pages auto-compute pct_tasks_affected via a `useEffect` on mount (both simple and advanced modes). Major category pills (occ explorer) and GWA pills (WA explorer) remain visible in simple mode
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

### Page: My Occupation (`/my-occupation` → `app/my-occupation/page.tsx`)

Thin wrapper that fetches `/api/config` and renders `<OccupationReport config={config} />`. No URL params — the component manages its own `selectedTitle` and `geo` state internally.

### Component: `OccupationReport`

Single-file component (`components/OccupationReport.tsx`) holding the entire report page. Sub-sections are local `function` components defined in the same file: chrome (`Picker`, `SearchPanel`, `BrowsePanel`, `BrowseSelect`, `PickerTab`), primitives (`Pill`, `MiniBar`, `TierDot`, `Sparkline`, `RiskGauge`, `SourceMiniBars`, `Chevron`, `Card`, `TierGroup`), top-of-page (`Hero`, `RiskFlagsTable`, `KpiRow`, `KpiCard`), body cards (`RankBars`, `SectorChain`, `SectorChainStat`, `TechList`, `TasksByTier`, `TaskRowsCompact`, `SkaSection`, `SkaSummaryStat`, `SkaSubsection`, `SkaTable`, `WaSection`, `WaByTier`, `WaTable`, `RankedCell`, `SimilarTable`), and footer (`PaletteLegend`, `PaletteFooter`, `Th`, `Td`).

**State:**
- `titles: string[]` — list of all 923 occupation titles, fetched once on mount.
- `selectedTitle: string` — current selection. `searchQuery` is a separate input string with typeahead suggestions.
- `geo: string` — geography code; changing triggers a refetch.
- `report: OccupationReport | null` — full payload from `/api/occupation-report`.
- `waLevel: "gwa" | "iwa" | "dwa"` — work activities tab.
- `showRiskFlags: boolean` — risk-tier "Why?" expandable inside the hero.

Each `Card` and `TierGroup` manages its own local `open: boolean` state for collapsibility.

**Layout** (top to bottom):
1. **Header** — page title + "all-confirmed" attribution paragraph (kept from prior version).
2. **Picker** — Search / Browse-by-category tabs + geography dropdown.
3. **Hero** — full-width card. Left: eyebrow ("Occupation report · {geo}"), occupation title, SOC chain, and four pills (Job Zone, Outlook, n_tasks, total workers). Right: tinted card with `RiskGauge` (108×~92px SVG, half-circle, score in center), tier label, "{n} of 8 flags raised" line, and a "Why?" toggle that reveals the 8-flag breakdown table.
4. **KPI row** — 4 cards in a `1.2fr 1fr 1fr 1fr` grid. First card has a brand-color left accent bar, the headline `% of weighted tasks affected` value at 38px, sub line ("Up from X% in YYYY-MM"), and an inline `Sparkline` of the all_confirmed trend. Other three: workers affected, wages affected, intensity rank.
5. **12-col body grid** of `Card` primitives, all collapsible at the section level via a chevron on the header:
   - `Where you rank` (colSpan 4) — gradient-filled bars for Economy / Major / Minor / Broad on % tasks, with workers/wages ranks below; intensity sub-card.
   - `Sector chain` (colSpan 4) — three stacked entries (Major / Minor / Broad) each from `report.sector_chain`. Per entry: name, rank pill, and a 3-column row of % tasks / workers / wages with their respective ranks.
   - `Tools you use` (colSpan 4) — full list of the occ's softwares, scrollable, sorted by commodity rank.
   - `Tasks AI can help with` (colSpan 12) — `PaletteLegend` then `TasksByTier`: tasks grouped into collapsible tier sections (high/mid/low/none) via `TierGroup`. Within each tier, `TaskRowsCompact` shows the existing rows (TierDot + task text + 4 source mini-bars + max score), click-to-expand for top MCP servers (only when present).
   - `Where you lead, where AI leads` (colSpan 12) — SKA section: 4-stat summary header, then three collapsible subsections (Skills, Knowledge, Abilities) via `SkaSubsection`. Each subsection groups its rows into the same 3 collapsible color-bucket tiers, then renders `SkaTable` with the existing 6 columns.
   - `Your work activities` (colSpan 12) — GWA / IWA / DWA tabs. Rows are tier-grouped via `WaByTier` and rendered by `WaTable`. Columns: name, # tasks (in occ), Conv/API/MS/MCP per-source maxes, then four `RankedCell` columns (eco % tasks, eco workers, eco wages, eco auto) — each value with its `#rank/total` underneath in muted small text.
   - `Similar occupations` (colSpan 12) — top-5 nearest by SKA L1 distance with the existing 7-column table.
6. **PaletteFooter** — original source-attribution paragraph at page bottom.

**Color tokens** (defined in-file): `BUCKET_BG / BUCKET_BORDER / BUCKET_DOT / BUCKET_FG / BUCKET_LABEL / BUCKET_TIER_HEADING` keyed by `ColorBucket` (`"high" | "mid" | "low" | "none"`). Same neutral 3-tier palette used for task auto_aug coloring (≥4 / 2.5–4 / <2.5), SKA pct_of_need coloring (≥100 / 66–100 / <66), and tier-group section headers. `TIER_COLORS` provides the 4 risk-tier colors used by the `RiskGauge` arc fill and the hero's right-rail card. `SOURCE_META` defines the four data-source colors used by `SourceMiniBars`.

**Collapsibility model:**
- Every body `Card` opens/closes via a chevron on its header (default open).
- `TierGroup` (used inside Tasks, SKA tables, and WA tables) opens/closes per tier (high/mid open by default, low/none closed by default) so users can scroll through long lists by ignoring the lower tiers.
- `SkaSubsection` adds a third nesting level: section → S/K/A subsection → tier group → table.

**Tasks table:** all unique tasks for the occ, grouped into 3 collapsible color-bucket tiers. The grid is `1fr 320px 80px 70px 60px 24px` (task text | per-source bars | freq×imp×rel value | rank-in-occ | max AI | chevron). Per-source mini-bars show numeric value (0–5) above each bar, labels spelled out as `Claude Conv` / `Claude API` / `Copilot` / `MCP`. The "Rank in occ" column color-intensity-codes the rank position (top tasks render bold/dark, bottom tasks render muted/light) so the load-bearing tasks pop visually. A header row at the top of the section labels each column. Click on a row with `top_mcps.length > 0` expands to show top-5 MCP servers; chevron on the right indicates expandability.

**Work activities section:** tab selector (GWA/IWA/DWA). Each WA is rendered as a two-row card (replacing the prior 10-column table): top row = TierDot + name + n_tasks; middle row = `SourceMiniBars` (per-source values for Claude Conv / Claude API / Copilot / MCP); bottom row = a horizontal pill strip of `EcoPill`s for the four economy-wide stats from `eco_stats` (Eco %, Workers, Wages, Auto), each pill carrying its `#rank/total` inline. Cards are still grouped into 3 collapsible color-bucket tiers via `WaByTier` → `WaList` → `WaCard`.

**SKA section:** three subsections (Skills, Knowledge, Abilities), each tier-collapsible. Sorted with biggest AI lead at the top within each tier. The summary header shows the four ratio-of-sums percentages (Overall / Skills / Knowledge / Abilities). Section title: "Where AI leads, where you lead".

**Software commodities section** (replaces the prior "Tools you use" list): aggregates the occupation's `tech` rows by `commodity`, dedups multiple software examples per commodity, and lists each commodity once with `(N tools)` count and `#rank/total` (commodity's economy-wide rank by avg pct_tasks_affected). Sorted by commodity rank ascending. Component: `TechCommodities`.

**Similar section:** top 5 nearest occupations by L1 distance. Columns: occupation, sector, **Exposure** (tier chip + 8 lit/unlit flag dots from `risk.flags`, all colored by tier), % tasks affected, median wage, job zone, outlook, SKA distance. Component: `ExposureProfile` renders the exposure cell.

**Hero / KPI labels:** all "Risk" UI strings render as "Exposure" — `TIER_COLORS` labels are "High Exposure / Mod-High Exposure / Mod-Low Exposure / Low Exposure" (with a `short` field used by the Similar table chip), the hero eyebrow on the gauge card reads "Exposure tier", and the "Why?" panel's intro paragraph reads "Exposure score is built from 8 binary flags…". The KPI row's fourth card is "AI adoption rank" (renamed from "Intensity rank") — same underlying `headline.intensity` data, just clearer copy describing per-task AI usage. Internal data fields (`risk.score`, `risk.tier`, `risk.flags`, `intensity.*`) keep their original names.

**No Simple/Advanced mode handling** — this page is a single curated view by design; the toggle in nav still appears (it's global) but the component doesn't read `useSimpleMode()`.

### Page: Occupation Categories (`/occupation-categories` → `app/occupation-categories/page.tsx`)

**Two-group (A/B) comparison with staged settings.**

State model:
- `pendingA/B` — form state (`GroupPending` interface: datasets, method, geo, aggLevel, topN, sortBy, physicalMode, useAutoAug, searchQuery, contextSize)
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

Fetches `config` only, passes to `ExplorerView`. Occupation and group data are fetched inside the component (geo-dependent).

### Page: Work Activities Explorer (`/wa-explorer`)

Fetches `config` only, passes to `WAExplorerView`. WA data is fetched inside the component (geo-dependent).

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

**Dataset selection:** Date range (from/to dropdowns from `getAllDates()`) plus sub_type pills grouped by category (Snapshots, Usage, Agentic, All) via `SubTypePillSelector`. User selects sub_type keys (e.g. "AEI Both + Micro", "MCP"). Backend receives sub_type keys as `series` parameter (matching keys in `DATASET_SERIES`). Frontend resolves sub_type keys + date range to dataset names via `getDatasetsInRange()` and filters `data_points` by `dp.dataset`. For WA Trends, AEI and non-AEI sub_types cannot be mixed (AEI uses eco_2015, non-AEI uses eco_2025); `familyRestriction` prop hides incompatible pills.

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

**Geography selector:** A `<select>` dropdown populated from `config.geo_options` (same pattern as ExplorerView/WAExplorerView). State is `string` (not a union type). Both OccupationTrends and WorkActivityTrends have independent geo state.

**Controls:** Collapsible sections (Datasets / Display / Filtering); TopN, Sort, Search, Value ranking, and Context controls always visible (do not require a Run first).

**Custom `ChartLegend`:** Grid of colored squares, clickable (click = lock). Shows increase badge per item. Passed to `downloadChartAsPng()` as `legendItems`.

### Component: `ExplorerView`

Props: `config: ConfigResponse`. Occupations, groups, and task data are fetched internally and re-fetched when `geo` changes.

**Flat table** with inline drilldown. No accordion.

**Column order at task level:** name, occ, broad, minor, major, dwa, iwa, gwa, emp, wage, phys (checkmark), freq, imp, rel, auto avg, auto max, auto avg (all), auto max (all), % phys, pct avg, pct max, pct avg (all), pct max (all), sum pct avg, sum pct max, % tasks aff, workers aff, wages aff. At non-task levels: name, job outlook (DWS star rating), emp, wage, # occs, # tasks, auto avg/max (with vals), auto avg/max (all), % phys, pct avg/max (with vals), pct avg/max (all), sum pct avg/max, % tasks aff, workers aff, wages aff.

**Columns hidden at task level:** `n_occs`, `n_tasks`, `auto_avg_all`, `auto_max_all`, `pct_phys`, `pct_avg_all`, `pct_max_all`, `sum_pct_avg`, `sum_pct_max`, `dws_star`, `job_zone` (`NON_TASK_COLS`). Columns hidden at non-task levels: `occ`, `major_cat`, `minor_cat`, `broad_cat`, `dwa_col`, `iwa_col`, `gwa_col`, `phys_col`, `freq_col`, `imp_col`, `rel_col` (`TASK_ONLY_COLS`).

**Simple mode task columns:** name, occ, major, gwa, emp, wage, auto avg, pct avg, % tasks aff, workers aff, wages aff (`SIMPLE_TASK_COLS`). **DWS Star Rating** (`dws_star` / "Job Outlook") and **Job Zone** (`job_zone`) are NOT in `SIMPLE_COLS`, so they are hidden in simple mode at non-task levels.

Levels: Major / Minor / Broad / Occupation / Task. At "Task" level, data fetched from `/api/explorer/all-eco-tasks` on first switch and cached.

**`FlatRow` interface:** holds all metric fields plus `sourceOccs: OccupationSummary[]` (for lazy drilldown), `level`, `dws_star_rating?: number | null` (DWS star rating, 1–5 for occupations, averaged for groups), and `job_zone?: number | null` (O*NET job zone, 1–5 for occupations, averaged for groups).

**Controls:**
- Multi-select major category pills (empty = all)
- Click-to-sort column headers (asc/desc toggle)
- Per-column ≥/≤ filter dropdowns (`ColumnFilterDropdown`)
- Search bar with level selector + text highlighting via `highlightText()`
- Avg/Max toggle (which auto_aug variant to display)
- Geography dropdown (populated from `config.geo_options`) for emp/wage
- **Sources selector** (hidden in simple mode): multi-select dropdown populated from `config.explorer_source_names`. Shows checkboxes for each AI source with an All/None toggle. Changing the selection triggers a refetch of explorer data. Default: all sources selected. When all sources are selected, the API is called without `selected_sources` (backend default = all). The `selectedSources` set is turned into a stable array via `useMemo` for use as an effect dependency.
- Auto-aug min sliders (with_vals and all_tasks variants)
- Reset button (resets level→major, pills→clear, search→clear, sort→emp desc, column filters→clear, expanded→collapse, geo→nat, physical→all, hiddenCols→defaults, minPct→0, pagination→100, and re-runs auto-compute with default settings)

**Column selector (gear icon):** Click-outside to close. At the task level, shows group toggle buttons: All/None (show/hide all columns), Occ +/− (toggle occ/broad/minor/major columns), WA +/− (toggle dwa/iwa/gwa columns). In Simple mode, only the curated subset columns (`SIMPLE_COLS` or `SIMPLE_TASK_COLS`) are selectable. Persisted to localStorage.

**Auto-compute on load:** A `useEffect` on mount runs the full compute pipeline with default settings (all datasets, freq, all phys, auto-aug on, Average) and populates `pctAffectedMap`. The pct columns (`pct_affected`, `workers_aff`, `wages_aff`) are always visible (showing "---" while loading). This runs in **both** simple and advanced modes. A `computeVersion` state counter allows the reset handler to force a re-run.

**Pagination:** `rowLimit` state (100 rows), "Load 100 more" footer. Resets on level/filter/search/sort changes.

**Child rows:** `childRowCache` — pre-built `useMemo` Map keyed by `"level:name"` for O(1) lookups. Rebuilt when groups/occupations change (data already reflects selected geo).

**Task expansion:** Clicking an occupation row fetches tasks via `fetchOccupationTasks()`. Task detail shows Occupation Classification (Broad → Minor → Major), Activity Classification (GWA/IWA/DWA), per-source breakdown table (AEI Conv. v1–v5, API v3–v5, MCP Cumul. v4, Microsoft, plus AVG and MAX summary rows). **AEI N/A handling:** When all AEI sources have null `auto_aug` and null `pct_norm` (task not in eco 2015 baseline), individual AEI source rows are collapsed into a single "AEI" row displaying "Not in task set" in italic.

**Occ-level emp:** Occupation Explorer at the occ level shows raw occupation employment (not divided by number of tasks).

**`PctComputePanel`:** Collapsible panel calling `/api/compute` with `aggLevel: "occupation"`, `topN: 1000`. Returns `Map<string, number>` (title → pct_tasks_affected). Adds a `minPctAffected` slider filter to the table. **Auto-recomputes** when the parent `geo` changes while a previous compute result exists (via `geoChangedRef` + `useEffect`).

**Major category pills** are always visible (including in simple mode).

**Task expansion section order:** Occupation Categories → Work Activities → Task Detail → Source Breakdown → Top MCP Servers. Task Detail shows: Emp, Wage, Physical, Freq, Imp, Rel (no auto/pct). Accordion task view (DWA expansion in WA explorer) shows the same plus auto avg/max and pct avg/max.

**Task-level columns:** `occ`, `broad_cat`, `minor_cat`, `major_cat`, `dwa_col`, `iwa_col`, `gwa_col`, `phys_col`, `freq_col`, `imp_col`, `rel_col` are available as table columns at the task level only (`TASK_ONLY_COLS`).

**`InfoTooltip`:** `createPortal(tooltip, document.body)` with `position: fixed` at mouse coords — avoids clipping by `overflow: hidden` ancestors.

**Formatters:**
- `fmtPctNorm(v)`: displays value directly as % (no ×100); `< 0.00001` → full decimal; `< 0.01` → `toPrecision(1)`; `≥ 0.01` → `toFixed(4)`
- `fmtAutoAug(v)`: `toFixed(3)`
- `fmtPctPhys(v)`: multiplies by 100 (stored as 0–1 fraction)

### Component: `WAExplorerView`

Props: `config: ConfigResponse`.

Fetches WA explorer rows internally via `fetchWAExplorer(geo, selectedSources)` — refetches when `geo` or `selectedSources` changes. Task-level eco data refetched via `fetchAllEcoTasks(geo, selectedSources)` on geo/sources change. DWA expansion tasks fetched via `fetchWAActivityTasks("dwa", name, geo)`.

Same general table structure as ExplorerView but hierarchy is GWA → IWA → DWA → Tasks. **AEI N/A handling:** Same collapsed "AEI → Not in task set" pattern as ExplorerView in both DWA task accordion and task-level expansion source breakdowns.

**Geo selector:** A `<select>` dropdown populated from `config.geo_options` (a `Record<string, string>` mapping geo code to display name). State is `string` (not a union type). Changing geo triggers refetch of WA rows, eco task rows, and auto-compute pct.

**Level selector:** GWA / IWA / DWA / Task. Task level uses the same all-eco-tasks dataset as ExplorerView (fetched per-geo from `/api/explorer/all-eco-tasks?geo=...`).

**Column order at task level:** name, occ, broad, minor, major, dwa, iwa, gwa, emp, wage, phys (checkmark), freq, imp, rel, auto avg, auto max, pct avg, pct max, % tasks aff, workers aff, wages aff. At non-task levels: name, emp, wage, # occs, # tasks, auto avg/max (with vals/all), % phys, pct avg/max (with vals/all), sum pct avg/max, % tasks aff, workers aff, wages aff. **Columns hidden at task level:** `n_occs`, `n_tasks`, `auto_avg_all`, `auto_max_all`, `pct_phys`, `pct_avg_all`, `pct_max_all`, `sum_pct_avg`, `sum_pct_max` (`NON_TASK_COLS`). **Simple mode task columns:** name, occ, major, gwa, emp, wage, auto avg, pct avg, % tasks aff, workers aff, wages aff (`WA_SIMPLE_TASK_COLS`).

WA Explorer task view uses weighted emp (freq or value based on Time/Value toggle). At task level, "name" is the task text and occ/broad/minor/major/dwa/iwa/gwa columns are populated.

**Sources selector** (hidden in simple mode): same multi-select dropdown as ExplorerView, populated from `config.explorer_source_names`. Changing selection triggers refetch of WA data and task data. Hidden in simple mode (all sources used by default).

**Column selector (gear icon):** Click-outside to close. At the task level, shows group toggle buttons: All/None, Occ +/−, WA +/− (same pattern as ExplorerView).
- Simple mode (non-task level): only `WA_SIMPLE_COLS` are selectable
- Simple mode (task level): only `WA_SIMPLE_TASK_COLS` are selectable
- Advanced mode: all columns selectable; selection persisted to localStorage

**Text column filters (`TextColumnFilterDropdown`):**
- Available for occ, major_cat, minor_cat, broad_cat, dwa_col, iwa_col, gwa_col columns
- Funnel icon in column header opens a multi-select dropdown of all unique values in that column
- Applied to `topRows` after numeric and text filters

**DWA row expansion (accordion):**
- Fetches task list via `/api/explorer/wa/tasks` (cached)
- Renders a `WATaskSubHeader` + `WATaskSubRow` per task (11 columns: Task, Emp, Wage, Phys, Freq, Imp, Rel, Auto Avg, Auto Max, Pct Avg, Pct Max)
- Uses weighted emp: freq-weighted or value-weighted based on the parent's Time/Value toggle (`empWeighting`)
- Each sub-row is itself expandable to show a Source Breakdown table (per-source auto-aug + pct with AVG/MAX footer rows) and a Top MCPs panel (if applicable)
- pct_affected is injected from `pctAffectedMap` — keyed by **DWA activity name** (not task text)

**Task-level expansion:**
- Expands to show Occupation Classification (occ → broad → minor → major), Activity Classification (GWA/IWA/DWA), Task Details panel (physical/freq/imp/rel/emp/wage only — auto/pct are already table columns), Source Breakdown (with AVG/MAX footer rows), and Top MCPs panel
- pct_affected injected via `pctAffectedMap.get(r.dwa_title ?? "")` — uses DWA title as key (not task text)

**`WaPctComputePanel`:** Same as ExplorerView `PctComputePanel` but calls `/api/work-activities` with the current WA settings. Injects pct/workers/wages columns. Dataset selection uses `enforceDatasetToggle` from `lib/datasetRules.ts`. Accepts an `empWeighting` prop — the panel's internal method is synced to the parent's empWeighting toggle ("freq" maps to "freq", "value" maps to "imp"). When the toggle changes and results already exist, the panel auto-recomputes. The `pctAffectedMap` is populated from **all three levels** (gwa + iwa + dwa) in the API response, so accordion children at any level can look up their pct values. Auto-compute on load uses the same approach — fetching all three levels and merging into the map.

**Emp weighting toggle:** An "Emp Weight" segmented control (Time / Value) next to other controls. Controls which emp allocation variant is displayed (`emp_freq` vs `emp_value`). Hidden in simple mode (defaults to freq/Time). Affects both activity-level and accordion task sub-rows. Also syncs the `WaPctComputePanel` method (freq/imp) and triggers auto-recompute of % Tasks Affected when results exist.

**Section titles in task expansions:** Occupation Categories, Work Activities, Task Detail, Source Breakdown, Top MCP Servers — consistent across both explorers.

**Accordion Task Detail (DWA expansion):** Shows Source Breakdown table (per-source auto-aug + pct with AVG/MAX footer rows) and Top MCPs. The sub-table row itself shows Task, Emp, Wage, Phys, Freq, Imp, Rel, Auto Avg, Auto Max, Pct Avg, Pct Max.

**Task-level Task Detail:** Shows Emp, Wage, Physical, Freq, Imp, Rel only (no auto/pct — those are already visible as table columns).

**GWA multi-select pills** (always visible, including simple mode), same sort/filter/search/pagination/Avg/Max/Nat/Utah patterns as ExplorerView.

### Component: `TaskChangesView`

`TaskChangesView.tsx` — Task-level dataset comparison table (titled "Task Changes Explorer"). Props: `config` (`ConfigResponse`). Dataset pickers, geography dropdown (populated from `config.geo_options`, state is `string`), status filter pills (with dynamic counts that update based on active filters), major category pills, search, per-column numeric threshold filters (funnel icon → min/max dropdown), per-column text filters (funnel icon → multi-select checkbox dropdown for Occupation, Major, Minor, Broad, GWA, IWA, DWA), column selector, pagination. Passes `geo` to `fetchTaskChanges()` and `fetchAllEcoTasks()` API calls. Task column uses word-wrap (no truncation); lowercase task names are auto-capitalized via `titleCaseTask()`. Column labels use "Auto" instead of "auto_aug". Source breakdown in expanded rows uses colored AVG/MAX badges matching explorer style. Table container has `maxHeight` with `overflowY: auto` so horizontal scroll is accessible from any vertical position. Row expansion ALWAYS shows occupation categories and work activities sections (even when values are null/dash), plus source breakdown and top MCP servers. When the "to" dataset starts with "AEI", section headers change to "2015 Occupation Hierarchy" and "2015 Task Hierarchy". Dataset pickers use the `DatasetSelector` component (category → sub_type → date cascading selection) sourced from `config.dataset_categories`. Default datasets: AEI Both 2025-03-06 → All 2026-02-18. **AEI N/A handling:** Same collapsed "AEI → Not in task set" pattern as ExplorerView (see above).

### Utility: `lib/datasetRules.ts`

Shared dataset selection enforcement. Exports:
- `DatasetClassification` interface: `{ aeiConvSnapshotDatasets, aeiApiSnapshotDatasets, aeiConvCumulativeDatasets, aeiApiCumulativeDatasets, aeiBothCumulativeDatasets, mcpDatasets }`
- `enforceDatasetToggle(current, name, cls)` — returns the new selection after toggling `name`, with family-based rules applied across 4 AEI families + MCP:
  - Selecting a **cumulative AEI** (from any cumulative family) → removes all other cumulative AEI and all snapshot AEI
  - Selecting a **snapshot AEI** (from any snapshot family) → removes all cumulative AEI
  - Selecting an **MCP** → removes all other MCP (only one MCP at a time)
  - Deselecting anything → always allowed
- `getDatasetConflictMessage(current, cls)` — returns a conflict description string or null if valid

Used by: `ExplorerView` `PctComputePanel`, `WAExplorerView` `WaPctComputePanel`, `occupation-categories/page.tsx` `DatasetPills`, `work-activities/page.tsx` `DatasetPillsWA`.

The classification arrays are sourced from `config.aei_conv_snapshot_datasets`, `config.aei_api_snapshot_datasets`, `config.aei_conv_cumulative_datasets`, `config.aei_api_cumulative_datasets`, `config.aei_both_cumulative_datasets`, `config.mcp_datasets` (from `GET /api/config`). The UI organizes datasets into subsections by family.

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
| `_dataset_cache` | `(file_path, is_aei, method, use_auto_aug, physical_mode, geo, agg_level)` | Single-dataset compute result |
| `_explorer_occ_cache` | singleton | 923 occupation summaries |
| `_explorer_task_cache` | `title` string | Task details per occupation |
| `_explorer_task_lookup_cache` | singleton | task_normalized → sources lookup |
| `_explorer_groups_cache` | singleton | Major/minor/broad group rows |
| `_wa_explorer_cache` | singleton | WA explorer rows (GWA/IWA/DWA) |
| `_all_tasks_cache` | singleton | All unique tasks with metrics |
| `_all_eco_task_rows_cache` | singleton | All ~23,850 eco_2025 task×occ rows with AI metrics |
| `_top_mcps_cache` | singleton | `task_normalized → [{title, url}]` from MCP Cumul. v4 top_mcps column |
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

9. **Trends backend receives sub_type keys as series names.** Frontend passes selected sub_type keys (e.g. "AEI Both + Micro", "MCP") directly; backend looks them up in `DATASET_SERIES`. Frontend resolves sub_type keys + date range → dataset names via `getDatasetsInRange()` and filters data_points accordingly.

10. **Trends cumulative max carries forward.** If a category has no data at a date, the running max from prior dates is used — it never decreases.

11. **Explorer child rows use `childRowCache` useMemo Map** (keyed `"level:name"`). Do NOT re-filter arrays inside render functions — use the pre-built cache.

12. **Explorer pagination is 100 rows at a time** for all levels. Never render all rows at once — occupation level has 923+ rows and DWA has hundreds, causing DOM jank with 10K+ nodes.

13. **Search inputs are debounced** (250–300ms via `useDebounce`) before inclusion in `topRows` useMemo deps. Do not use raw input state in useMemo deps.

14. **Filter icon (`FunnelIcon`) in explorer column headers must be `position: absolute`** inside the `<th>`. Placing it inside the inline-flex label div pushes column text and overflows into adjacent columns.

15. **`InfoTooltip` uses `createPortal` into `document.body`** — required to avoid clipping by `overflow: hidden` ancestors. Position is `fixed` at mouse coordinates.

16. **`AllTaskRow.emp/wage` are allocated values** — computed as `Σ(emp_occ / n_unique_tasks_per_occ)` across sharing occupations for the requested geography. Not the same as occupation-level employment totals.

17. **`pct_physical` is stored as a 0–1 fraction.** `fmtPctPhys(v)` multiplies by 100 for display.

18. **Overview/WA pages use staged settings.** `pending*` is form state; `fullResponse*` is backend results (topN=1000); `displayResponse*` is client-filtered. Charts only update on "Run" click.

19. **Explorer column filter dropdowns require `overflow: visible` on `<th>`.** The `ColumnFilterDropdown` and `TextColumnFilterDropdown` use `position: absolute` with `top: 100%` inside header cells. If the `<th>` has `overflow: hidden`, the dropdown is clipped and invisible. Additionally, add `onClick` and `onMouseDown` `stopPropagation()` on dropdown root divs to prevent click-through to the `<th>` sort handler.

20. **`ColumnFilterDropdown` must use functional updater form properly.** The `setMinMax` callback must read `prev[colKey]` (not a stale closure `cur`) to prevent one field overwriting the other during batched React updates.

19. **Trends frozen tooltip:** `lockedPos` is screen-space; the fixed `<div>` must be clamped to `window.innerHeight/innerWidth` to stay on-screen. Always shows all lines at the locked date (sorted by value desc, scrollable). A `dotClickedRef` flag prevents the parent div click handler from clearing the lock when clicking a dot.

20. **DWA emp allocation in WA Explorer** deduplicates on `(title_current, task_normalized)` within each activity — not globally. Each activity level (GWA/IWA/DWA) deduplicates independently.

21. **All 8 sources are shown in explorer task breakdowns** (AEI Conv. v1–v4, AEI API v3–v4, MCP Cumul. v4, Microsoft) — not just latest versions.

22. **Explorer `PctComputePanel`** calls `/api/compute` with `aggLevel: "occupation"`, `topN: 1000`. Physical filter affects numerator only, consistent with the rest of the app.

23. **Currency formatting is adaptive.** `fmtChartValue` (HorizontalBarChart) and `fmtVal` (TrendsView) display wages in billions ($B) when ≥ $1B, millions ($M) when ≥ $1M, thousands ($K) when ≥ $1K, otherwise raw dollars. TrendsView values are already divided by 1e9 before reaching `fmtVal`, so thresholds are 1 / 0.001 / 0.000001. Explorer `wages_aff` cells use the same adaptive logic.

24. **Auto-compute explorer pct on load (both modes).** `ExplorerView` runs a `useEffect` on mount (regardless of simple/advanced mode) that calls `fetchCompute` with preset settings (all datasets, freq, all phys, auto-aug on, Average) to populate `pctAffectedMap`. The pct columns (`pct_affected`, `workers_aff`, `wages_aff`) are always visible (showing "---" while loading). A `computeVersion` state counter in the dependency array allows the reset handler to force a re-run. `WAExplorerView` similarly auto-computes on mount, fetching all three levels (gwa/iwa/dwa) into `pctAffectedMap` so results persist across level switches. The `PctComputePanel` UI is hidden in simple mode.

25. **`pctAffectedMap` in WAExplorerView is keyed by DWA activity name, not task text.** At the DWA level the map key is `r.name` (the DWA name). At the Task level each row's `r.name` is the task text — use `r.dwa_title ?? ""` as the lookup key to find the parent DWA's pct_affected. Using `r.name` at task level produces no matches.

26. **Dataset selection enforcement is client-side only.** `enforceDatasetToggle()` in `lib/datasetRules.ts` auto-deselects conflicting datasets in the UI. The backend does not enforce these rules — any combination technically computes, but the results are only meaningful when selection constraints are respected (e.g., AEI Cumul. Conv. v4 already includes v1–v3, so selecting multiple cumulative versions from the same family is redundant).

27. **Cumulative AEI datasets cannot be mixed with snapshot AEI datasets.** Cumulative families (`AEI Cumul. Conv.`, `AEI API Cumul.`, `AEI Cumul. (Both)`) and snapshot families (`AEI Conv.`, `AEI API`) are mutually exclusive. The cumulative versions aggregate all conversations up to their snapshot date, so their scale is not comparable to the per-snapshot versions.

28. **Explorer source selection caches are keyed by `frozenset|None`.** `_explorer_occ_base_cache`, `_explorer_groups_base_cache`, `_wa_explorer_geo_cache`, and `_all_eco_tasks_geo_cache` are dict caches keyed by the selected sources parameter (a frozenset of source names, or None for "all"). When adding new parameters that change metric outputs, ensure the cache key includes them.

28. **WA emp allocation is method-weighted, not equal-split.** The backend returns both freq-weighted and value-weighted emp variants for WA explorer rows and WA task details. The frontend emp weighting toggle selects which variant to display. The WA charts page's Time/Value method toggle controls both task_comp AND emp weighting simultaneously.

29. **PctComputePanel auto-recomputes on geo and empWeighting changes.** Both `PctComputePanel` (occ explorer) and `WaPctComputePanel` (WA explorer) track `geo` changes via a ref and auto-recompute when the panel has already been computed and the geo changes. `WaPctComputePanel` additionally auto-recomputes when the parent's `empWeighting` toggle changes (syncing "freq"/"value" to the panel's "freq"/"imp" method). Simple mode auto-compute handles geo via its useEffect dependency.

30. **All-eco-tasks uses weighted emp, not n_tasks_per_occ.** `get_all_eco_task_rows(geo)` returns weighted emp allocation fields (`emp_freq`, `emp_value`) for the requested geography instead of `n_tasks_per_occ`. The WA Explorer task view selects freq or value variant based on Time/Value toggle. The `get_wa_explorer_data(geo)` `needed_cols` includes `freq_mean`, `relevance`, `importance` — all three are required for correct emp allocation and to avoid emp=0 bugs for WA activity rows.

31. **`occupation_report.py` re-implements analysis logic instead of importing it.** The Dockerfile only ships `data/`, `backend/`, and a hand-picked subset of `analysis/data/` CSVs. Importing from `analysis.*` Python modules in the backend works locally but breaks in production. So `_compute_ska_for_pct`, `_equal_consensus_bias_ratios`, the risk-table flag logic, and the intensity ratio pipeline are inlined in `occupation_report.py`. If the analysis canonical implementations change (e.g. `analysis/data/compute_ska.py` SKA formula, `analysis/exploratory/audit_pct_norm_eco/run.py` GWA share constants, or the risk-flag spec in `analysis/ANALYSIS_ARCHITECTURE.md`), update both places.

32. **`AEI Both + Micro 2026-02-12` is the source of truth for the Occupation Report.** `PRIMARY_DATASET = "AEI Both + Micro 2026-02-12"` drives every headline number, the SKA pipeline, the risk score, the intensity rank, and the tech commodity ranking. Per-task auto_aug per source still comes from the regular explorer task lookup (which reads AEI Conv. v1–v5, AEI API v3–v5, MCP Cumul. v4, Microsoft directly). When/if a newer snapshot lands, change the `PRIMARY_DATASET` constant and `TREND_SERIES` together — they share the same all_confirmed family.
