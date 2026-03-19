# CLAUDE.md — AEA Dashboard

Full technical reference for the Automation Exposure Analysis Dashboard.
**Goal:** Help a new Claude Code session understand the whole project without needing to read every file.

---

## Project Overview

Interactive web dashboard comparing AI automation exposure across occupation groups, task hierarchies, and time.
Built for the Anthropic Economic Index (AEI) project; intended for Utah's Office of Artificial Intelligence Policy (OAIP).

**Tech stack:** FastAPI (Python 3.12) backend + Next.js 14 / React 18 / TypeScript frontend.
**Deployed:** Railway (backend via Docker) + Vercel (frontend static export).

---

## Directory Structure

```
aea_dashboard/
├── backend/
│   ├── main.py          — FastAPI app, all API endpoints
│   ├── compute.py       — Core compute engine (all data processing logic)
│   └── config.py        — Dataset registry, paths, constants
├── frontend/
│   ├── package.json
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx              — Root layout with <Navigation />
│       │   ├── globals.css             — Design system (CSS vars, utility classes)
│       │   ├── page.tsx                — Overview page (two-group bar charts)
│       │   ├── work-activities/page.tsx — DWA/IWA/GWA activity charts
│       │   ├── trends/page.tsx         — Time-series trends
│       │   ├── explorer/page.tsx       — Job explorer (table view)
│       │   └── wa-explorer/page.tsx    — WA Explorer (new, 5th tab)
│       ├── components/
│       │   ├── Navigation.tsx          — Sticky top nav (5 tabs)
│       │   ├── GroupPanel.tsx          — Container for one group's 3 bar charts (Overview)
│       │   ├── HorizontalBarChart.tsx  — Recharts horizontal bar chart with rich tooltip
│       │   ├── WorkActivitiesPanel.tsx — DWA/IWA/GWA Recharts charts (pure renderer)
│       │   ├── TrendsView.tsx          — Line-chart trends page (2 tabs)
│       │   ├── ExplorerView.tsx        — Table-only occupation explorer (overhauled)
│       │   └── WAExplorerView.tsx      — WA Explorer: GWA/IWA/DWA hierarchy table (new)
│       └── lib/
│           ├── types.ts         — All TypeScript interfaces
│           ├── api.ts           — All fetch functions (wraps FastAPI)
│           └── downloadChart.ts — PNG download utility for chart containers
├── data/                — CSV data files (see section below)
├── Dockerfile           — Multi-stage build; copies backend/ + data/; runs uvicorn
├── railway.json         — Railway: dockerfile builder
├── requirements.txt     — Python deps (fastapi, uvicorn, pandas, numpy)
└── .python-version      — 3.12
```

---

## Running Locally

```bash
# Backend
cd aea_dashboard
venv/Scripts/python -m uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev      # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` if needed (default).

---

## Data Files (`data/`)

| File | Rows | SOC | Key columns |
|------|------|-----|-------------|
| `final_eco_2025.csv` | 23,850 | 2019 | **ECO baseline** (denominator for all metrics); has `task_prop`, `title_current` |
| `final_eco_2015.csv` | 24,631 | 2010 | **ECO baseline for AEI work-activity analysis**; has `title` (2010 SOC) |
| `final_aei_v1–v4.csv` | ~5K each | 2010 | `title` (2010 SOC), no `auto_aug_mean_adj`; needs crosswalk to 2019 |
| `final_aei_api_v3–v4.csv` | ~5K each | 2010 | Same schema as AEI |
| `final_mcp_v1–v4.csv` | ~15K each | 2019 | `title_current`, has `auto_aug_mean_adj` |
| `final_microsoft.csv` | ~10K | 2019 | `title_current`, no `auto_aug_mean_adj` |
| `2010_to_2019_soc_crosswalk.csv` | 1,164 | — | Searched in `data/` first, then `../aea_dashboard_dev/data/` |

**Shared columns across all datasets:**
- `task`, `task_normalized` — O*NET task text
- `dwa_title`, `iwa_title`, `gwa_title` — O*NET work activity hierarchy
- `freq_mean` (0–10), `importance` (0–5), `relevance` (0–100) — O*NET survey
- `auto_aug_mean` (0–5) — AI automatability score (all datasets)
- `auto_aug_mean_adj` — MCP only; excludes flagged ratings (preferred for MCP)
- `pct_normalized` — share of conversations for this task (AEI/MCP/Microsoft only; all zeros in ECO files); **values are already in percent form (e.g., 0.4 means 0.4%, NOT 40%)**
- `physical` — boolean; truly physical task
- `date` — dataset snapshot date (used for time-trend analysis)
- `emp_tot_nat_2024`, `emp_tot_ut_2024` — employment (BLS OEWS 2024)
- `a_med_nat_2024`, `a_med_ut_2024` — median annual wage (BLS OEWS 2024)

**ECO 2015 note:** `auto_aug_mean` and `pct_normalized` are all null/zero — values must be fetched from AEI/MCP/MS datasets by `task_normalized` lookup.

**Dataset dates (for trend analysis):**
- AEI v1: 2024-12-23 | v2: 2025-03-06 | v3: 2025-08-11 | v4: 2025-11-13
- AEI API v3: 2025-08-11 | v4: 2025-11-13
- MCP v1: 2025-04-24 | v2: 2025-05-24 | v3: 2025-07-23 | v4: 2026-02-18
- Microsoft: 2024-09-30

---

## Backend Architecture

### `config.py`
- `DATASETS` — dict of all 11 selectable datasets (no Eco 2015 for users)
- `ECO_2015_META` — internal reference used only for work-activity AEI baseline
- `DATASET_SERIES` — groups datasets by family: `{"AEI": ["AEI v1"…v4], "MCP": ["MCP v1"…v4], …}`
- `AGG_LEVEL_COL` — maps `"major"/"minor"/"broad"/"occupation"` → column name
- `SORT_COL_MAP` — maps human-readable sort label → column name

### `compute.py` — Key Functions

**Occupation-level (Overview page):**
- `load_eco_baseline(method, physical_mode, geo)` — loads & caches eco_2025 deduped by (title_current, task_normalized), computes eco task_comp (no auto_aug)
- `compute_task_comp(df, method, use_auto_aug, use_adj_mean)` — freq: `freq_mean`; imp: `relevance × 2^importance`; × `auto_aug_mean/5` if requested
- `compute_single_dataset(...)` — full pipeline for one dataset; AEI gets crosswalk + split_count normalization + task_prop deflation; cached
- `aggregate_results(...)` — computes pct/workers/wages at occupation then rolls up to requested agg_level; also computes per-category rank columns (`rank_workers`, `rank_wages`, `rank_pct`)
- `combine_results(...)` — outer-join multi-dataset results; Average or Max
- `get_group_data(settings)` — orchestrates pipeline for one sidebar group; returns top-N rows sorted descending, plus `total_categories`, `total_emp`, `total_wages`, `matched_category` (for search highlight)

**Work Activities (DWA/IWA/GWA):**
- `compute_work_activities(settings)` — splits selected datasets into AEI group (eco_2015 baseline) and MCP/Microsoft group (eco_2025 baseline); calls `_compute_wa_for_group` for each
- `_compute_wa_for_group(dataset_names, settings, use_eco2015)` — deduplicates eco on (title, task_normalized), counts unique tasks per occ for emp allocation, joins AI data, computes per-task worker contributions, aggregates by GWA/IWA/DWA

**Work Activity computation detail:**
- pct_tasks_affected per activity = Σ(AI task_comp for tasks in that activity) / Σ(ECO task_comp for tasks in that activity) × 100
- emp_per_task = emp_occ / n_unique_task_occ_pairs (NOT counting DWA duplicates)
- workers_contribution per task = (AI_tc / ECO_tc) × emp_per_task  → summed by activity group
- A task mapping to multiple DWAs contributes its full amount to each DWA (they're independent; not double-counting)

**Trends:**
- `compute_trends(settings)` — for each selected series, runs `compute_single_dataset` for every version, records date, returns time series per category. `TrendSeries.data_points[i].dataset` is the individual dataset name (e.g. "AEI v2").

**Explorer — new functions (Stop 5):**

- `AEI_EXPLORER_DATASETS` — constant: `["AEI v1", "AEI v2", "AEI v3", "AEI v4", "AEI API v3", "AEI API v4"]`; used for all explorer lookups (not just v4)

- `_build_explorer_task_lookup()` — builds a dict `task_normalized → {source_name: {"auto_aug": float|None, "pct_norm": float|None}}` for all 8 sources (6 AEI + MCP v4 + Microsoft). AEI values are averaged across all 2010 SOC occupations sharing that task. MCP uses `auto_aug_mean_adj`. Cached in `_explorer_task_lookup_cache`.

- `_compute_task_metrics(task_norms, lookup)` — given a list of task_normalized values and the lookup dict, returns 10 metrics:
  - `auto_avg_with_vals` — per-task avg across sources, then averaged over tasks **with at least one value**
  - `auto_max_with_vals` — per-task max across sources, then averaged over tasks with values
  - `auto_avg_all` — same but over **all tasks** (nulls counted as 0)
  - `auto_max_all` — same but max variant over all tasks (nulls = 0)
  - `pct_avg_with_vals`, `pct_max_with_vals` — same pattern for pct_norm
  - `pct_avg_all`, `pct_max_all` — same over all tasks
  - `sum_pct_avg`, `sum_pct_max` — sum of per-task avg/max pct across tasks with values

- `get_explorer_occupations()` — builds list of all 923 eco_2025 occupations with hierarchy, emp, wage, `n_tasks`, `n_physical_tasks`, `pct_physical`, and 10 metric fields. Uses `_build_explorer_task_lookup()` + `_compute_task_metrics()`. Cached.

- `get_explorer_groups()` — pre-computes major/minor/broad aggregations. For each group, collects **unique task_norms** across all occupations in the group (not averages of occ-level averages). Calls `_compute_task_metrics()` on those unique tasks. Returns `{major: [...], minor: [...], broad: [...]}` with parent/grandparent hierarchy fields and `n_occs`. Cached in `_explorer_groups_cache`.

- `get_occupation_tasks(title)` — returns all tasks for one occupation sorted alphabetically by `task` column. Uses all 8 AEI/MCP/MS sources. `sources` dict keyed by source name. Returns `avg_pct_norm` and `max_pct_norm` (not `avg_pct_normalized`). Cached per title.

- `get_all_tasks()` — returns all unique task_normalized values across eco_2025 with their metrics (from `_compute_task_metrics`) and activity hierarchy columns. Used for the Task-level flat table in the Explorer. Cached.

- `get_wa_explorer_data()` — builds GWA/IWA/DWA rows. Emp is allocated as `emp_occ / n_unique_tasks_in_occ` per task. Activity levels deduplicate differently:
  - GWA: dedup on (task_norm, gwa_title)
  - IWA: dedup on (task_norm, iwa_title)
  - DWA: dedup on (task_norm, dwa_title)
  Returns all rows in one flat list with `level` field. Cached in `_wa_explorer_cache`.

- `get_wa_tasks_for_activity(level, name)` — returns task details for one GWA/IWA/DWA activity, fetching AI metrics from the lookup. Cached per (level, name).

**Caching:** All expensive computations are cached in module-level vars. The explorer occupations list is precomputed on first `/api/explorer` call (~2-3s). Individual occupation task lookups are cached on demand.

### `main.py` — API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check |
| GET | `/api/config` | Datasets, availability, series, agg levels |
| POST | `/api/compute` | Occupation-level chart data (Overview) |
| POST | `/api/work-activities` | DWA/IWA/GWA activity data |
| POST | `/api/trends` | Time-series data per dataset series |
| POST | `/api/wa-trends` | Work-activity time-series data |
| GET | `/api/explorer` | Full occupation list with 10 metric fields (no tasks) |
| GET | `/api/explorer/tasks?title=…` | Task details for one occupation (all 8 sources) |
| GET | `/api/explorer/groups` | Pre-computed major/minor/broad group rows |
| GET | `/api/explorer/all-tasks` | All unique tasks with metrics (for Task level table) |
| GET | `/api/explorer/wa` | WA Explorer rows: GWA/IWA/DWA with emp + metrics |
| GET | `/api/explorer/wa/tasks?level=…&name=…` | Task details for one WA activity |

`/api/compute` accepts optional `searchQuery` and `contextSize` params in the body; returns `matched_category` in response.
`/api/config` returns `dataset_series` and `eco2015_available` fields.

---

## Frontend Architecture

### Navigation
5-tab sticky top nav at `var(--nav-height): 56px`. Pages use `height: calc(100vh - 56px)`.
- **Occupation Categories** (`/`) — two-group occupation bar charts
- **Work Activities** (`/work-activities`) — DWA/IWA/GWA charts, same two-group layout
- **Trends** (`/trends`) — line charts of metrics over dataset versions
- **Job Explorer** (`/explorer`) — flat table: Major/Minor/Broad/Occ/Task levels with inline drilldown
- **WA Explorer** (`/wa-explorer`) — GWA/IWA/DWA hierarchy table with inline drilldown

### Design System (`globals.css` + `tailwind.config.ts`)
CSS variables:
```css
--brand: #1a6b5a        /* deep teal — primary action color */
--brand-hover: #155749
--brand-light: #e8f5f1  /* teal tint for active states */
--bg-base: #f7f7f4      /* cream off-white page background */
--bg-surface: #ffffff   /* card/panel background */
--bg-sidebar: #fafaf8
--border: #e4e4de
--border-light: #eeeeea
--text-primary: #1a1a1a
--text-secondary: #5a5a5a
--text-muted: #9b9b9b
--nav-height: 56px
```
Group A color: `#3a5f83` (slate blue) | Group B: `#4a7c6f` (sage green)
Utility classes: `.card`, `.pill`, `.btn-brand`, `.btn-ghost`, `.filter-chip`, `.tag`, `.tag-aei`, `.tag-mcp`, `.tag-ms`, `.tag-avg`, `.tag-max`

### TypeScript Interfaces (`lib/types.ts`)

**Shared metrics base (`ExplorerMetrics`):**
```ts
interface ExplorerMetrics {
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
```

Key interfaces: `GroupSettings`, `ConfigResponse`, `ChartRow`, `ComputeResponse`, `ActivityRow`, `ActivityGroup`, `WorkActivitiesResponse`, `TrendsSettings`, `WATrendsSettings`, `TrendsResponse`, `TrendSeries`, `TrendDataPoint`, `OccupationSummary extends ExplorerMetrics`, `TaskDetail`, `OccupationTasksResponse`, `ExplorerGroupRow extends ExplorerMetrics`, `ExplorerGroupsResponse`, `AllTaskRow`, `WAExplorerRow extends ExplorerMetrics`, `WAExplorerResponse`, `WATaskDetail`, `WATasksResponse`

**`TaskDetail`:** `sources: Record<string, TaskSourceStats>` (keyed by source name, e.g. "AEI v1", "MCP v4", "Microsoft"); `avg_pct_norm` and `max_pct_norm` (not `avg_pct_normalized`).

### State Pattern (Overview + Work Activities)
Staged settings: `pendingA/B` (form state) + `appliedA/B` (chart state). Charts only update on "Run" click. This prevents recomputation on every slider move.

**Occupation Categories (`page.tsx`):**
- `GroupPending` interface holds all per-group settings: datasets, combineMethod, method, geo, aggLevel, topN, sortBy, physicalMode, useAutoAug, useAdjMean, searchQuery, contextSize
- A/B tab toggle lets user switch which group's settings are shown; "Sync B → A" copies group A settings to B
- `run()` calls `Promise.all([fetchCompute(settingsA), fetchCompute(settingsB)])` so both groups update simultaneously
- `otherResponse` is passed between GroupPanels for cross-group delta in tooltips
- `appliedPendingA/B` state stored at run time; `pendingToConfigSummary()` converts it to 2 config lines passed to `GroupPanel` as `configSummary`

**Work Activities (`work-activities/page.tsx`):**
- `WAGroupPending` interface similar to `GroupPending` but with `activityLevel: "gwa"|"iwa"|"dwa"` instead of `aggLevel`
- Mutual exclusivity enforced client-side: mixing AEI-family and MCP/Microsoft-family datasets shows a warning and blocks the API call
- Search is entirely client-side — backend returns all activity rows, frontend slices ±contextSize around the matched row
- `appliedPendingA/B` state + `pendingToConfigSummary()` same pattern as Occupation Categories; passed to `WorkActivitiesPanel` as `configSummary`

---

## Component Details

### `HorizontalBarChart.tsx`
- Recharts `BarChart` with `layout="vertical"` (horizontal bars)
- Rich tooltip shows all 3 metrics (workers, wages, % tasks), rank within economy, economy share %, and delta vs other group
- Bars sorted descending (highest = top). `matchedCategory` bar rendered orange with others dimmed
- `totalCategories`, `totalEmp`, `totalWages` passed in for rank/share calculations (summed across ALL categories, not just top-N)

### `GroupPanel.tsx`
- Pure renderer: receives `response`, `otherResponse`, `loading`, `error`, `matchedCategory`, `configSummary?: string[]`
- Renders 3 ChartCards (Workers, Wages, % Tasks) each with a download button
- Passes `otherGroupRows` from `otherResponse` to `HorizontalBarChart` for delta tooltip
- `configSummary` is passed to `downloadChartAsPng` as `configLines` → rendered as footer in the PNG

### `WorkActivitiesPanel.tsx`
- Pure renderer: receives `response: WorkActivitiesResponse | null`, `activityLevel`, `searchQuery`, `contextSize`, `configSummary?: string[]`
- `response.aei_group ?? response.mcp_group` determines which data to show
- Client-side `applySearch()` finds the matched row by `includes()`, slices ±contextSize, returns `matchedCategory`
- Renders 3 ChartCards (Workers, Wages, % Tasks) per group
- `configSummary` passed to download as footer

### `downloadChart.ts`
- `LegendItem` interface: `{ color: string; label: string; extra?: string }`
- `downloadChartAsPng(el, filename, opts)` options: `{ title?, configLines?, legendItems? }`
- Renders legend as grid on canvas: colored circle + truncated label + extra badge; `LEGEND_COLS = min(4, floor(w/210))`
- Renders config lines as small grey text below a separator, after the legend
- Old approach cloned SVG only; new approach renders everything on canvas so HTML legend is captured

### `TrendsView.tsx`
Two tabs: **Occupation Categories** and **Work Activities**

**Dataset selection:** Individual dataset pills (e.g. "AEI v1", "AEI v2", …) rather than family toggles. Backend still receives family names (derived from selected datasets via `getSeriesToFetch`), but `data_points` are filtered client-side by `dp.dataset` matching selected individual datasets.

**Line modes (3 options):**
- `individual` — one line per (dataset × category); `buildIndividualData()` filters data_points to selected datasets
- `average` — one line per category; at each date, averages values across all selected datasets present at that date; `buildAggregatedData(..., "average")`
- `max` — **cumulative running max** per category; value at date T = max(all dataset values at dates ≤ T); implemented with `runningMax` Map that carries forward; `buildAggregatedData(..., "max")`

**Controls:** Row 1–3 (shown before run): dataset pills, line mode, method, physical, auto-aug, geo, top-N, Run. Row 4 (shown only after run): Sort (by value / by increase), Increase type (abs/%), Search category, Context ± slider.

**Sort by increase:** `computeIncreases()` computes Map<lineKey, increase> from first to last data point in each line. `sortedCats` sorted by max increase per category when `sortMode === "increase"`. `shownCats` filters by search ± ctxSize.

**Hover + lock:** `hoveredLine` state + `lockedLine` state. `activeLine = lockedLine ?? hoveredLine`. Clicking an `activeDot` toggles `lockedLine`. Active line gets `strokeWidth` 3.5; dimmed lines 1.5; others 2.5. Tooltip shows only active line when focused.

**Custom `ChartLegend` component:** Grid layout replacing Recharts `<Legend>`. Colored square indicators, clickable (click = lock), shows increase badge per item. Passed as `legendItems` to `downloadChartAsPng` for capture in PNG.

### `ExplorerView.tsx` (overhauled — table only)
Props: `occupations: OccupationSummary[]` + `groups: ExplorerGroupsResponse` + `config: ConfigResponse`.
The accordion view has been removed. This is now a flat sortable/filterable table with inline drilldown.

**Formatters:**
- `fmtPctNorm(v)` — displays value directly as % (no ×100); `< 0.00001` → full decimal; `< 0.01` → `toPrecision(1)`; `≥ 0.01` → `toFixed(4)`
- `fmtAutoAug(v)` — `toFixed(3)`
- `fmtPctPhys(v)` — multiplies by 100 for display (this field is stored as 0–1 fraction)

**`COLUMNS` array (16 columns):** Name, Emp, Med Wage, # Occs (group levels), # Tasks, Auto Avg↑, Auto Max↑, Auto Avg (all), Auto Max (all), % Phys, Pct Avg↑, Pct Max↑, Pct Avg (all), Pct Max (all), Σ Pct Avg, Σ Pct Max

**`FlatRow` interface:** holds all metric fields plus `sourceOccs: OccupationSummary[]` (for lazy drilldown) and `level: "major"|"minor"|"broad"|"occupation"|"task"`.

**Level selector:** Major / Minor / Broad / Occupation / Task. At "Task" level, data is fetched from `/api/explorer/all-tasks` on first switch and cached in `taskData` state.

**Pagination (`rowLimit` state):** All levels are paginated to 100 rows at a time with a "Load 100 more →" footer. `rowLimit` resets to 100 whenever level, filters, search, or sort changes. This keeps the DOM small (~100 `<tr>` × 16 columns) regardless of level size, preventing scroll jank with 900+ occupation rows.

**`buildChildRows(row, level)`:** uses `childRowCache` (a pre-built `useMemo` Map keyed by `"level:name"`) for O(1) child lookups. Previously filtered arrays on every render; now computed once when `groups`/`occupations`/`geo` change.

**Controls:**
- Multi-select major category pills (empty set = show all)
- Sort by any column (click header to sort asc/desc; clicking same column toggles direction)
- Per-column ≥/≤ filter dropdowns (`ColumnFilterDropdown` component)
- Search bar with level selector (All / Major / Minor / Broad / Occ / Task) + text highlighting via `highlightText()`
- Avg/Max toggle (controls which auto_aug variant is used for the "Auto Avg↑"/"Auto Max↑" display and filters)
- Nat/Utah toggle for emp/wage columns
- Auto-aug min slider (two sliders: one for "with vals" variant, one for "all tasks" variant)
- Reset button clears all filters/sort/search/selections

**Performance notes:**
- `search`, `minEmp`, `minWage` are debounced (250–300ms) via `useDebounce` before being used in `topRows` useMemo deps — prevents recompute on every keystroke
- `topRows` useMemo rebuilds only when debounced values or other stable deps change
- All rendering is paginated via `rowLimit` (see above) — never render all 923 occupation rows at once

**`InfoTooltip` component:** Uses `createPortal(tooltip, document.body)` with `position: fixed` at mouse coordinates to avoid clipping by `overflow: hidden` parent containers.

**Recursive `renderRow(row, level, indent)`:** renders a table row, and if expanded, its children inline with indentation. At occupation level, fetches tasks via `fetchOccupationTasks()` on expand.

**Task detail expansion:** Expanding a task row shows Activity Classification (GWA/IWA/DWA) and per-source breakdown table with all AEI versions listed individually (v1–v4, API v3–v4) plus MCP v4 and Microsoft, plus AVG and MAX summary rows.

**`PctComputePanel` component (retained):**
- Collapsible panel with full compute settings: dataset selector, method, physical, auto-aug, adj mean
- "Compute %" button calls `fetchCompute` with `aggLevel: "occupation"`, `topN: 1000`
- Returns `Map<string, number>` (occupation title → pct_tasks_affected) via `onResult` callback
- `minPctAffected` slider appears in table controls once map is computed

### `WAExplorerView.tsx` (new)
Props: `rows: WAExplorerRow[]`

Displays GWA → IWA → DWA hierarchy with inline drilldown, same 16-column structure as ExplorerView.

**Controls:**
- Level selector: GWA | IWA | DWA (filters which rows are shown as top-level)
- GWA multi-select pills (empty = all)
- Sort by any column (click header)
- Per-column ≥/≤ filter dropdowns
- Avg/Max toggle, Nat/Utah toggle
- Auto-aug min slider (with_vals and all_tasks variants)

**Hierarchy:** When a GWA row is expanded, its IWA children appear inline; IWA expansion shows DWA children; DWA expansion fetches tasks via `fetchWAActivityTasks("dwa", name)` and shows a task sub-table.

**Task sub-table (under DWA):** shows task, physical flag, activity hierarchy, per-source breakdown, avg/max auto_aug, pct norm columns. Source breakdown expansion mirrors ExplorerView.

**Pagination (`rowLimit` state):** Same 100-row-at-a-time pattern as ExplorerView. `rowLimit` resets on level/filter/search/sort changes. "Load 100 more →" footer appears when `topRows.length > rowLimit`.

**`getChildRows(parentRow)`:** uses `childRowCache` (pre-built `useMemo` Map keyed by `"level:name"`) for O(1) IWA/DWA child lookups instead of O(n) array filtering on every render.

**`search` debounced** 250ms via `useDebounce` before use in `topRows` useMemo deps.

**Emp computation:** `emp_nat` / `emp_ut` on WA rows represent emp_occ / n_unique_tasks summed over all occs in that activity — same allocation logic as the WA page backend.

**`InfoTooltip`:** same portal pattern as ExplorerView.

---

## Key Algorithms

### Task Completion Computation
```
freq method:  task_comp = freq_mean
imp method:   task_comp = relevance × 2^importance
with auto-aug: task_comp × (auto_aug_mean / 5)   [MCP uses auto_aug_mean_adj]
```

### Occupation-level Metrics
```
pct_tasks_affected = Σ(AI task_comp) / Σ(ECO task_comp) × 100  [ratio-of-totals, never average of %]
workers_affected   = pct/100 × emp
wages_affected     = pct/100 × emp × median_wage
```

### Search / Context Window (Overview)
Backend sorts all categories descending, finds the index of the matched category (case-insensitive `contains`), slices rows `[idx - contextSize : idx + contextSize + 1]`, and returns `matched_category` string. Frontend highlights that bar orange and dims others.

### AEI Crosswalk Pipeline
AEI uses 2010 SOC titles. Steps to convert to 2019 SOC:
1. Dedup AEI on (title, task_normalized)
2. Join crosswalk → O*NET-SOC 2019 Title
3. Divide task_comp and emp by split_count (# 2019 titles per 2010 title)
4. Group by (2019_title, task_normalized): sum task_comp, sum emp
5. Deflate task_comp by task_prop from eco_2025 (accounts for 2025 vs 2010 task set)

### Work Activity (DWA/IWA/GWA) Allocation
AEI group uses eco_2015 (2010 SOC); MCP/Microsoft group uses eco_2025 (2019 SOC).
```
n_tasks_per_occ  = count of unique (title, task_normalized) pairs in eco baseline
emp_per_task     = emp_occ / n_tasks_per_occ
workers_for_task = (AI_tc / ECO_tc) × emp_per_task  (summed by DWA/IWA/GWA)
```
A task mapping to multiple DWAs contributes its full emp allocation to each DWA group independently.

### Trends — Individual Dataset Filtering
The backend receives series family names (e.g. `["AEI", "MCP"]`) derived from whatever individual datasets the user selected. It returns all versions within those families. The frontend then filters each `TrendSeries.data_points` by `dp.dataset in selectedDatasets` before building chart data. This means selecting "AEI v2" only shows the v2 data point even though the backend computed v1–v4.

### Explorer Metrics Computation (`_compute_task_metrics`)
Given a set of `task_norms` and the lookup dict:
```
For each task:
  per_task_avg = mean of non-null auto_aug values across all sources
  per_task_max = max of non-null auto_aug values across all sources

auto_avg_with_vals = mean(per_task_avg) over tasks where per_task_avg is not null
auto_max_with_vals = mean(per_task_max) over tasks where per_task_max is not null
auto_avg_all       = mean(per_task_avg OR 0) over ALL tasks
auto_max_all       = mean(per_task_max OR 0) over ALL tasks
(same pattern for pct_norm variants)
sum_pct_avg        = sum(per_task_avg pct) over tasks with values
sum_pct_max        = sum(per_task_max pct) over tasks with values
```

For group-level rows (major/minor/broad/GWA/IWA/DWA), task_norms are collected as **unique values across all occupations/activities** in the group — not averaged from sub-group metrics.

### pct_normalized Display
Values in CSV are already in percent form (e.g., 0.4 means 0.4%). Do **not** multiply by 100 before display. `fmtPctNorm(v)` uses `v` directly:
- `v < 0.00001` → full decimal string + `%`
- `v < 0.01` → `toPrecision(1)` + `%`
- `v >= 0.01` → `toFixed(4)` + `%`

---

## Deployment

**Backend → Railway:**
- `Dockerfile`: multi-stage Python 3.12; copies `backend/` + `data/`; runs `uvicorn backend.main:app`
- `railway.json`: `{"build": {"builder": "DOCKERFILE"}}`
- Port: from `$PORT` env var

**Frontend → Vercel:**
- Next.js 14 static/SSR export
- Set `NEXT_PUBLIC_API_URL` to Railway backend URL
- Vercel reads `frontend/` as root

---

## Common Pitfalls

1. Don't show Eco 2015 as a selectable dataset to users — it's only an internal baseline for work-activity AEI analysis
2. AEI files use `title` (2010 SOC); MCP/Microsoft use `title_current` (2019 SOC) — don't mix them without crosswalk
3. The crosswalk CSV lives in `data/` or `../aea_dashboard_dev/data/` — checked automatically
4. `pct_normalized` and `auto_aug_mean` are **zero/null in eco_2025 and eco_2015** — must come from AI datasets
5. For work activities, the eco_2025 denominator DWA associations come from eco_2025 itself (not the AI dataset)
6. For trends, `compute_single_dataset` is reused — its results are cached by full parameter tuple
7. The explorer `/api/explorer` precomputes 923 occupation summaries on first call — allow ~3–5s on cold start
8. Work Activities: mixing AEI-family and MCP/Microsoft-family datasets in the same group is blocked by client-side `isMixed()` check — they use different ECO baselines (2015 vs 2025) so results are not comparable
9. Trends backend receives series **family** names even though the UI shows individual dataset pills — `getSeriesToFetch()` maps selected individual datasets → families before the API call
10. `ComputeResponse.total_emp` and `total_wages` are sums across ALL categories (before top-N filter) — used for economy-share % in tooltips, not just the visible bars
11. The first nav tab is named **"Occupation Categories"** (not "Overview") — the route is still `/`
12. Trends cumulative max carries forward: if a category has no data at a given date, the running max from prior dates is used — it never decreases
13. Explorer flat table drilldown stores `sourceOccs` on each `FlatRow`. Child rows (major→minor→broad→occ) are pre-built in a `childRowCache` useMemo Map (keyed `"level:name"`) that recomputes when groups/occupations/geo change — do not re-filter group arrays inside render functions
14. Explorer `PctComputePanel` calls `/api/compute` with `aggLevel: "occupation"` at `topN: 1000` to get all occupations; physical filter here affects numerator only, consistent with the rest of the app
15. **`pct_normalized` is already in % form** — do not multiply by 100. `fmtPctNorm(v)` displays `v` directly.
16. Explorer group metrics (major/minor/broad) are pre-computed from unique task_norms across all occs in the group — never average the per-occupation metric values, as that produces incorrect results
17. ExplorerView accordion view was removed in Stop 5 — the component is table-only; `groups: ExplorerGroupsResponse` is now a required prop for the pre-computed group rows
18. All 8 sources are shown in explorer task breakdowns (AEI v1–v4, AEI API v3–v4, MCP v4, Microsoft) — not just the latest versions
19. WA Explorer emp allocation uses `emp_occ / n_unique_tasks` per task — same logic as the WA page backend; each activity level deduplicates tasks independently (IWA on task_norm+iwa_title, DWA on task_norm+dwa_title)
20. InfoTooltip uses `createPortal` into `document.body` — required to avoid clipping by `overflow: hidden` ancestor containers; tooltip position is `fixed` at mouse coordinates
21. Explorer tables use `rowLimit` (100) pagination for **all** levels — never render all rows at once. The occupation level has ~923 rows and DWA has hundreds; rendering them all causes 10K+ DOM nodes and scroll jank. Always slice `topRows.slice(0, rowLimit)` before rendering.
22. Explorer search/text inputs are debounced (250–300ms) via `useDebounce` before being included in `topRows` useMemo deps — do not add raw input state directly to useMemo dependency arrays or every keystroke will trigger a full filter+sort pass
