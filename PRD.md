# PRD — Automation Exposure Analysis Dashboard

Product Requirements Document · Single source of truth for what the product is and does.

---

## 1. Product Overview

The Automation Exposure Analysis Dashboard measures how AI capabilities map onto the U.S. occupational task structure. It answers the question: **for a given occupation, work activity, or job category, what share of the work could be affected by current AI systems — and how many workers and wage dollars does that represent?**

Built for Utah's Office of Artificial Intelligence Policy (OAIP) as part of a research project for measuring AI's workforce impact. The intended audience is policymakers, workforce analysts, and informed members of the public. Researchers trying to replicate the data pipeline have other resources they can look at for this information.

The dashboard is a web application with a FastAPI backend and a Next.js frontend, deployed on Railway (backend) and Vercel (frontend).

---

## 2. Data Sources

The dashboard draws on five independent data sources. Using multiple AI scoring sources is a deliberate design choice: no single model or methodology fully captures AI capability, so triangulating across sources gives a more robust and defensible picture.

### AI Scoring Sources

Datasets are organized into four categories:

**Snapshots** — Single-point-in-time AI scoring datasets:
- **AEI Conv. v1–v5** — Five snapshot versions of Anthropic Economic Index conversation data spanning December 2024 to February 2026. Each O*NET task has an automatability score (0–5) based on the averages of the collaboration patterns observed in Claude interactions. Uses 2010 SOC codes (crosswalked to 2019 SOC).
- **AEI API v3–v5** — Three snapshot versions of AEI API/tool-use interaction data. Same scoring methodology as AEI Conv. but from programmatic API usage. Uses 2010 SOC codes (crosswalked to 2019 SOC).
- **Microsoft** — A single September 2024 assessment of AI exposure across occupations from Microsoft on Copilot usage. Automation scores are based on the average of the percent of a work activity's work that could be automated by the demonstrated use of the AI in a given conversation. Uses 2019 SOC codes natively.

**Usage** (cumulative) — Cumulative datasets tracking confirmed AI usage over time. Each date version accumulates all interactions up to that point:
- **AEI Both + Micro** — All confirmed usage: AEI conversation + API data, crosswalked to 2019 SOC and combined with Microsoft. Six date versions (Sep 2024–Feb 2026). Uses 2019 SOC.
- **AEI Conv + Micro** — All confirmed human usage: AEI conversation-only data, crosswalked to 2019 SOC and combined with Microsoft. Six date versions. Uses 2019 SOC.
- **AEI Both** — AEI conversation + API data (no Microsoft). Five date versions (Dec 2024–Feb 2026). Uses 2010 SOC (crosswalked).
- **AEI Conv** — AEI conversation-only data (no Microsoft). Five date versions. Uses 2010 SOC (crosswalked).
- **AEI API** — AEI API-only data. Three date versions. Uses 2010 SOC (crosswalked).

**Agentic** (cumulative) — Datasets capturing agentic AI tool-use capability:
- **MCP + API** — All possible agentic usage: MCP server logs combined with AEI API data. Seven date versions (Apr 2025–Feb 2026). Uses 2019 SOC.
- **MCP Cumul. v1–v4** — Standalone MCP server pipeline data. Four cumulative versions from April 2025 to February 2026. Uses 2019 SOC codes natively.

**All** (cumulative) — Combined across all source families:
- **All** — AEI Both + MCP + Microsoft combined. Ten date versions (Sep 2024–Feb 2026). Uses 2019 SOC.

### Structural & Economic Sources

**O*NET (2025 and 2015)** — The U.S. Department of Labor's Occupational Information Network provides the task inventory (what work each occupation involves), the work activity hierarchy (GWA → IWA → DWA), and survey-derived measures of task frequency, importance, and relevance. The 2025 edition is the primary task baseline; the 2015 edition is used as the baseline for AEI work-activity analysis (since AEI uses 2010 SOC codes that align with the older task set).

**BLS Occupational Employment and Wage Statistics (OEWS 2024)** — Employment counts and median annual wages by occupation, available at national level and for all 50 U.S. states, D.C., and select territories (Guam, Puerto Rico, U.S. Virgin Islands). These figures translate percentage-based exposure into concrete worker and dollar impacts.

---

## 3. Pages & Features

The dashboard has eight pages accessible from the top navigation bar. The **default landing page** is the Occupation Explorer (`/explorer`); the root URL (`/`) redirects there. A global **footer** below all page content shows source attribution and links to the project's GitHub repositories (dashboard, MCP classification, data pipeline), and a contact email.

### 3.1 Occupation Explorer

A sortable, filterable data table covering all 923 occupations in the O*NET/BLS universe, with pre-computed AI exposure metrics drawn from all ten baseline AI dataset sources (AEI Conv. v1–v5, AEI API v3–v5, MCP Cumul. v4, Microsoft). Users can control which sources contribute to these metrics via the Sources selector. The Pct Compute Panel additionally supports all user-selectable datasets including cumulative AEI and MCP versions.

**What questions it answers:**
- Which specific occupations or occupational categories have the highest AI exposure scores?
- How does exposure vary across the SOC hierarchy (major category → minor → broad → individual occupation → individual task)?
- For a given occupation, which of its tasks are most exposed and which AI sources agree?

**What the user sees and can do:**
- A table with columns for name, **Job Outlook (Utah)** (Utah DWS star rating, 1–5; averaged at group levels, shown to 1 decimal; hidden at task level and in simple mode), **Job Zone** (O*NET job zone, 1–5; averaged at group levels, shown to 1 decimal; hidden at task level and in simple mode), employment, median wage, number of occupations (at group levels), number of tasks, four auto-aug score variants (avg/max, with values only or across all tasks), percent physical, four pct_normalized variants, and two sum-of-pct columns. At the Task level, the column order is: name, occupation, broad, minor, major, DWA, IWA, GWA, emp, wage, physical (checkmark), freq, imp, rel, auto avg, auto max, pct avg, pct max, % tasks aff, workers aff, wages aff. The "% Tasks Affected" column shows "—" at the task level since the metric does not apply to individual tasks; Workers Affected and Wages Affected still display values. Group-level columns (# occs, # tasks, auto/pct "all" variants, % phys, sum pct) are hidden at task level.
- A **column selector** (gear icon in the header bar) that lets users toggle which columns are visible. Click-outside closes the panel. At the task level, includes All/None, Occ, and WA group toggle buttons. Persisted to localStorage. In Simple mode, only a curated subset is selectable (at task level: name, occ, major, GWA, emp, wage, auto avg, pct avg, % tasks aff, workers aff, wages aff).
- A **level selector** (Major / Minor / Broad / Occupation / Task) that controls the granularity of the table. At the Task level, each row is one task × occupation combination from the full ECO 2025 dataset (~23,850 rows). Tasks can repeat across occupations but each row has a unique combination of task, occupation, and work activity classification. Employment and wage columns show the raw occupation-level numbers (not divided).
- **Inline drilldown**: clicking any row expands it to show child rows at the next level down. At the occupation level, expanding shows individual tasks. At the task level, expanding a row shows five sections: **Occupation Categories** (Occupation → Broad → Minor → Major), **Work Activities** (GWA / IWA / DWA), **Task Detail** (Emp, Wage, Physical, Freq, Imp, Rel — no auto/pct since those are already table columns), **Source Breakdown** (per-source scores from all ten AI sources plus computed AVG and MAX summary rows; if a task is not in the eco 2015 task set, AEI sources collapse into a single "AEI — Not in task set" row), and **Top MCP Servers** (if available).
- **Multi-select major category pills** to filter to specific SOC major groups. At the task level, filtering applies to the task's `major_occ_category`.
- **Click-to-sort** on any column header (toggles ascending/descending).
- **Per-column threshold filters** via a filter icon on each column header (set ≥ or ≤ cutoffs).
- **Search** with a level-scope selector (All / Major / Minor / Broad / Occ / Task) and text highlighting on matches. At the task level, search also matches against occupation name and occupation classification columns.
- **Geography dropdown** switching employment and wage figures between geographies (populated dynamically from backend `geo_options`).
- **Sources selector** (advanced mode only) — a multi-select dropdown that controls which AI dataset sources (AEI Conv. v1–v5, AEI API v3–v5, MCP, Microsoft) contribute to the auto-aug and pct metric columns. All sources are selected by default. Users can toggle individual sources on/off or use the All/None button. Changing the selection triggers a data refetch. Hidden in simple mode (all sources used).
- **Pct Compute Panel** — an optional expandable panel that runs the full computation pipeline (with configurable dataset, combine option, method, physical filter, and auto-aug settings) and overlays "% Tasks Affected", "Workers Affected", and "Wages Affected" columns directly in the table. This lets users see the dashboard's computed metrics alongside the raw pre-computed scores. If the user changes the geography dropdown while results are already computed, the panel auto-recomputes with the new geography.
- **Row count display** — "Showing X of Y rows" is displayed at the top of the table (visible without scrolling) as well as at the bottom.
- **Pagination** — rows load 100 at a time with a "Load 100 more" button.

### 3.2 Work Activities Explorer

The same sortable/filterable table interface as the Occupation Explorer, but organized around O*NET's three-level work activity hierarchy instead of occupations.

**What questions it answers:**
- Which types of work activities (e.g., "Analyzing Data or Information", "Communicating with Supervisors") are most AI-exposed?
- How does exposure differ between broad activity categories (GWA) and their specific sub-activities (IWA, DWA)?

**What the user sees and can do:**
- A **level selector** (GWA / IWA / DWA / Task) controlling which tier of the hierarchy is shown as top-level rows. The Task level shows all ~23,850 eco rows (same data as the Occupation Explorer task level).
- **Inline drilldown**: GWA rows expand to show IWA children; IWA rows expand to show DWA children; DWA rows expand to show individual tasks with an accordion sub-table (column order: Task, Emp, Wage, Phys, Freq, Imp, Rel, Auto Avg, Auto Max, Pct Avg, Pct Max). Each task sub-row is expandable to show Source Breakdown (per-source auto-aug + pct with AVG/MAX footer rows) and Top MCP Servers. Task-level rows expand to show Occupation Categories, Work Activities, Task Detail (Emp, Wage, Physical, Freq, Imp, Rel only — auto/pct are already table columns), Source Breakdown (with AVG/MAX footer rows), and Top MCP Servers.
- **Emp weighting toggle** ("Emp Weight: Time / Value") — controls how employment is allocated to tasks within work activities (freq-weighted or freq×rel×imp-weighted). Hidden in simple mode (defaults to Time/freq). Affects both activity-level rows and accordion task sub-rows. Synced with the Pct Compute Panel's method (Time→freq, Value→imp); changing the toggle auto-recomputes % Tasks Affected when results already exist.
- **GWA multi-select pills** for filtering to specific General Work Activity groups. Scrollbar is visible for horizontal overflow.
- **Sources selector** (advanced mode only) — same multi-select dropdown as the Occupation Explorer, controlling which AI dataset sources contribute to auto-aug and pct metric columns. Hidden in simple mode (all sources used).
- **Column selector** (gear icon) — same as Occupation Explorer: toggles column visibility, persisted to localStorage. In Simple mode, only a curated subset of columns is selectable (different sets at the WA level vs. task level).
- **Text column filters** (multi-select dropdown) on the Occupation, Major, Minor, Broad, DWA, IWA, and GWA columns at the task level — lets users filter to specific occupational or activity categories by clicking a funnel icon in the column header.
- **Row count display** — "Showing X of Y rows" at the top and bottom of the table, same as Occupation Explorer.
- Same column structure (including task-level Occupation/Major/Minor/Broad and DWA/IWA/GWA columns), sorting, filtering, search, Avg/Max toggle, Nat/Utah toggle, and pagination as the Occupation Explorer. Task-level search also matches occupation name and classification columns. At the task level, "% Tasks Affected" shows "—" (same as Occupation Explorer).

### 3.3 Occupation Categories

A side-by-side comparison view with two independently configurable groups (A and B), each rendering three horizontal bar charts: Workers Affected, Wages Affected, and % Tasks Affected.

**What questions it answers:**
- Which occupation categories have the most workers, wages, and tasks exposed to AI?
- How do results change when you use different datasets, methods, or filters?
- How does one dataset's view of AI exposure compare to another's?

**What the user sees and can do:**
- **Two-group layout** — Group A and Group B side by side. Each group has its own independent control panel.
- **Dataset selection** — single dataset per group via cascading category → sub_type → date picker (using the `DatasetSelector` component sourced from `config.dataset_categories`).
- **Display controls** — method (Time or Value), geography (all states, populated from backend `geo_options`), aggregation level (Major / Minor / Broad / Occupation), and Top N (up to 30).
- **Filtering controls** — physical task filter (all / exclude physical / physical only), auto-aug multiplier toggle (Off / On).
- **Run button** — charts only update on Run, not on every control change. After running, control sections collapse to a summary bar.
- **Search** — type a category name to find it in the ranked list. The matched bar is highlighted orange with surrounding context bars shown (±N configurable).
- **Sort** — by Workers Affected, Wages Affected, or % Tasks Affected.
- **Rich tooltips** — hovering a bar shows its rank and pct in the full economy in workers, wages and tasks affected. And for each those it also shows the % change from the other chart group.
- **Sync B → A** button copies Group A's settings to Group B.
- **PNG download** per chart, with legend and configuration summary embedded in the image.

### 3.4 Work Activities

Same two-group comparison layout as Occupation Categories, but results are aggregated over work activities (GWA / IWA / DWA) instead of occupation groups.

**What questions it answers:**
- Which work activities are most affected by AI across the economy?
- How do AEI-derived activity exposure scores compare to MCP-derived ones?

**Key differences from Occupation Categories:**
- **Activity level** selector (GWA / IWA / DWA) instead of aggregation level.
- **Family restriction** — AEI-family datasets and MCP/Microsoft-family datasets cannot be mixed in the same group because they use different task baselines (O*NET 2015 vs. 2025). The UI enforces this and shows a warning if the user tries to mix.
- **Client-side search** — the backend returns all activity rows; the frontend handles search and context slicing.
- **Rich tooltips** — same as Occupation Categories: hovering a bar shows all 3 metrics (workers, wages, % tasks) with rank within the economy, economy share %, and delta vs the other chart group.

### 3.5 Trends

Time-series line charts showing how automation exposure metrics have changed across dataset snapshot dates.

**What questions it answers:**
- Is AI exposure growing over time for specific occupations or activities?
- Which categories have seen the biggest increases in exposure?
- How do different dataset families' trends compare?

**What the user sees and can do:**
- **Two tabs**: Occupation Categories and Work Activities, each with independent controls.
- **Dataset pills** — select individual dataset versions (e.g., "AEI Conv. v2", "MCP Cumul. v3", "AEI Cumul. (Both) v4") to include. Only selected versions appear as data points on the chart. The cumulative families are separate series from their snapshot counterparts.
- **Three line modes**: *Individual* (one line per dataset × category), *Average* (averages across selected datasets at each date), and *Max* (cumulative running maximum — the line never decreases).
- **Display controls** — metric (workers, wages, tasks), method (freq, imp), geography, aggregation level, Top N (up to 30), physical, auto-aug toggle.
- **Sort modes** — sort categories by current value or by increase (absolute or percentage change from first to last data point).
- **Search + context** — find a specific category and show ±N surrounding categories.
- **Hover + lock interaction** — hovering highlights a line; clicking a data point locks the line focus and freezes a tooltip panel near the click point showing all lines' values at that date (sorted by value, scrollable). The locked tooltip persists until clicked again or clicked elsewhere. Active lines render thicker; others are dimmed.
- **Sort and search controls** — visible on page load (do not require a Run first).
- **Custom legend** — clickable colored squares; clicking locks to that line. Shows increase badge per item.
- **PNG download** with legend captured.

### 3.6 Task Changes Explorer

A task-level comparison view that shows what changed between two dataset versions — which tasks were added, removed, or had score changes.

**What questions it answers:**
- What specific tasks drove changes between two dataset versions?
- Which tasks were newly rated, removed, or had score changes?
- For cross-family comparisons (e.g., AEI vs MCP), which tasks exist only in one family's baseline?

**What the user sees and can do:**
- **Dataset pickers** — cascading category → sub-type → date selectors (using the DatasetSelector component) for "From" and "To", then click Run to compare. Default: AEI Both 2025-03-06 → All 2026-02-18.
- **Status summary** — colored pills showing counts for each status: New (green), Changed (orange), Removed (red), Unchanged (grey), Not in baseline (muted/italic). Each pill toggles visibility of that status. Default: New + Changed + Removed visible. **Counts are dynamic** — they update based on active filters (major pills, search, physical filter, column filters), excluding the status filter itself.
- **Table** with default visible columns: Task, Occupation, Status, From Auto, To Auto, Δ Auto. Available via column selector: Major, Minor, Broad, GWA, IWA, DWA, Physical, Freq, Importance, Relevance, Emp, Wage, From pct, To pct, Δ pct. Task column displays full text (word-wrapping enabled, no truncation). Lowercase task names (from AEI data) are auto-capitalized.
- **Row expansion** — clicking a row shows occupation categories (labeled "2015 Occupation Hierarchy" when the to-dataset is AEI), work activities (labeled "2015 Task Hierarchy" when the to-dataset is AEI), source breakdown (all 10 AI sources with colored AVG/MAX badges matching explorer style; if a task is not in the eco 2015 task set, AEI sources collapse into a single "AEI — Not in task set" row), and top MCP servers.
- **When GWA/IWA/DWA columns are toggled on**, rows expand to unique (task, occupation, activity) combinations using eco_2025 data.
- **Δ columns** — green if positive, red if negative, "—" if either side is null.
- **Per-column threshold filters** — funnel icon on numeric column headers opens a min/max filter dropdown (same pattern as Occupation and WA Explorers).
- **Text column filters** — funnel icon on text columns (Occupation, Major, Minor, Broad, GWA, IWA, DWA) opens a multi-select checkbox dropdown to filter to specific values.
- **Filters** — status pills, major category pills, search across task/occupation/activity text, per-column numeric/text filters, physical filter (advanced only).
- **Scrollable table** — horizontal and vertical scroll available from any position (max-height container), not just at the bottom.
- **Pagination** — same 100-row pattern as other explorers.
- **Cross-family comparisons** — AEI data is crosswalked to 2019 SOC before comparison. "Not in baseline" status identifies tasks that couldn't have been rated by the other dataset family.

**Status logic:**
- **New** — task-occ exists in "to" dataset and in "from" dataset's eco baseline, but "from" didn't rate it.
- **Removed** — task-occ exists in "from" dataset and in "to" dataset's eco baseline, but "to" didn't rate it.
- **Changed** — both datasets rated it, auto_aug scores differ.
- **Unchanged** — both datasets rated it, same auto_aug score.
- **Not in baseline** — task-occ doesn't exist in the other dataset's eco baseline (cross-family only).

### 3.7 Instructions

A concise reference page with brief descriptions of each dashboard page and what it's for. Includes an AI-generated content disclaimer at the top linking to the GitHub repository for deeper technical detail. No formulas, calculators, or detailed methodology — those live on the About page.

### 3.8 About

A page summarizing the project's purpose, full computation methodology with equations for every derived metric (task_comp, auto-aug multiplier, % tasks affected, workers affected, wages affected, multi-dataset combination, explorer metrics, group-level aggregation, work activity employment allocation), and data source descriptions. Includes an AI-generated content disclaimer at the top linking to the GitHub repository. Identifies the dashboard as built for Utah's OAIP as part of a research project for measuring AI's workforce impact.

---

## 4. Core Metrics

### % Tasks Affected
The share of an occupation's total weighted task completion that is attributable to AI-exposed tasks.

Computed as the ratio of AI-weighted task completion to baseline (ECO) task completion: `sum of AI task weights / sum of ECO task weights × 100`. This is always a ratio-of-totals, never an average of percentages. The ECO baseline represents the occupation's full task profile without any AI scoring applied.

### Workers Affected
The number of workers in an occupation whose work is partially AI-exposed. Computed as `(% Tasks Affected / 100) × total employment`. This does not mean these workers will be replaced — it means this fraction of the workforce's aggregate task load overlaps with current AI capability.

### Wages Affected
The dollar volume of wages associated with AI-exposed task work. Computed as `(% Tasks Affected / 100) × employment × median annual wage`. Displayed with adaptive units: billions ($B) when ≥ $1B, millions ($M) when ≥ $1M, thousands ($K) when ≥ $1K, otherwise raw dollars.

### Auto-Aug Score (Automatability / Augmentation)
A 0–5 scale rating of how automatable or augmentable a specific task is by AI. Scores come from the AI dataset sources (AEI, MCP, Microsoft). When the auto-aug multiplier is enabled, each task's weight is scaled by `auto_aug_mean / 5`, so tasks rated as highly automatable contribute more to the exposure calculation and tasks rated as minimally automatable contribute less.

### Pct (Share of AI Conversations)
The percentage of AI conversations (from AEI/MCP/Microsoft data) that involved a given task. Values are already in percent form (e.g., 0.4 means 0.4%). This measures how frequently AI systems are actually being used for a task, as opposed to the auto-aug score which measures capability.

### Decimal Formatting
- **Auto-aug scores**: 1 decimal place (e.g., 3.2)
- **Pct (share of conversations)**: 4 decimal places (e.g., 0.0042)
- **MCP server ratings**: 1 decimal place
- **Freq, importance, relevance**: 1 decimal place

---

## 5. Key Configuration Options

| Option | Values | What it controls |
|--------|--------|-----------------|
| **Dataset selection** | AEI Conv. v1–v5, AEI API v3–v5, AEI Cumul. Conv. v1–v5, AEI API Cumul. v4–v5, AEI Cumul. (Both) v3–v5, MCP Cumul. v1–v4, Microsoft | Which AI scoring source(s) to use (26 total). Different sources capture different AI capabilities. Datasets are organized in the UI under labeled subsections: AEI Conversation, AEI API, AEI Cumul. (Both), MCP, Microsoft. Selection rules by family: **AEI Conv. family** — only one cumulative at a time; can't mix snapshots with cumulative. **AEI API family** — same rules. **AEI Cumul. (Both) family** — only one at a time; if selected, blocks ALL other AEI datasets. **MCP family** — only one at a time. Cross-family mixing is allowed (e.g., AEI Conv. v2 + AEI API Cumul. v5 is fine). The UI auto-deselects conflicting choices when a new dataset is added. |
| **Combine method** | Average / Max | When multiple datasets are selected, whether to average their scores or take the maximum per task. Max shows peak capability across sources; Average shows consensus. |
| **Method** | Time / Value | How task weights are computed. Time uses reported task frequency directly (`freq_mean`). Value uses `freq_mean × relevance × importance`, giving more weight to tasks that are frequently performed and are both important and relevant. On Work Activities pages, the method toggle also controls how employment is allocated to tasks (freq-weighted or freq×rel×imp-weighted). |
| **Geography** | Dynamic (from backend `geo_options`) | Which BLS employment and wage figures to use. Options are configured on the backend (e.g., National, Utah, California). |
| **Aggregation level** | Major Category / Minor Category / Broad Occupation / Occupation | The SOC hierarchy level at which to group and display results. Major has ~23 groups; Occupation has 923. |
| **Physical task filter** | All / Exclude physical / Physical only | Whether to include, exclude, or isolate tasks classified as requiring physical presence gotten from Microsoft's data for their AI analysis. Useful for focusing on cognitive/informational work. |
| **Auto-aug multiplier** | Off / On | When On, scales each task's contribution by its AI automatability score (0–5, normalized to 0–1). Off treats all AI-flagged tasks equally regardless of how automatable they are. |
| **Top N** | 1–30 | How many categories to display in charts (the top N by the selected sort metric). |
| **Sort by** | Workers Affected / Wages Affected / % Tasks Affected | Which metric determines the ranking of displayed categories. |
| **Search + Context** | Text query + ±N context size | Finds a specific category and shows it with N surrounding categories in the ranked list. |
| **Simple / Advanced mode** | Toggle in navigation bar | Switches the entire dashboard between a simplified view (fewer controls, preset defaults) and the full advanced view. See §5.1. |

### 5.1 Simple / Advanced Mode

A global toggle in the navigation bar switches the dashboard between **Simple** and **Advanced** mode. The toggle state is persisted in localStorage so it survives page reloads. Switching modes preserves all advanced settings — toggling back to Advanced restores the user's previous configuration.

**Simple mode effects by page:**

| Page | Fixed settings | Shown controls | Hidden |
|------|---------------|----------------|--------|
| **Occupation Explorer** | AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft on Average, Time, All phys, Auto-aug On, all sources | Level selector (Task hidden), Major pills, Search, Geo dropdown | Physical toggle, Sources selector, Min filters, PctComputePanel UI (auto-computed), Task level |
| **WA Explorer** | AEI Cumul. (Both) v4, Time, All phys, Auto-aug On, Emp Weight: Time, all sources | Level selector (Task hidden), GWA pills, Search, Nat/Utah | Physical toggle, Sources selector, Emp Weight toggle, PctComputePanel UI (auto-computed), Task level |
| **Occupation Categories** | AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft on Average, Time, All phys, Auto-aug On, single group | Aggregation, Geo, Sort, Search, Top N | Group B, Dataset/Method/Physical/Auto-aug controls |
| **Work Activities** | AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft on Average, Time, All phys, Auto-aug On, single group | Activity level, Geo, Sort, Search, Top N | Group B, Dataset/Method/Physical/Auto-aug controls |
| **Trends (Occ)** | All datasets, Time, All phys, Auto-aug On | Lines (Avg/Max only), Metric, Aggregation, Geo, Top N, Sort, Search | Datasets, Filtering, Individual line mode, Value ranking (auto-matches line mode) |
| **Trends (WA)** | All AEI datasets, Time, All phys, Auto-aug On | Lines (Avg/Max only), Metric, Activity level, Geo, Top N, Sort, Search | Datasets, Filtering, Individual line mode, Value ranking |
| **Task Changes Explorer** | AEI Both 2025-03-06 → All 2026-02-18 | Dataset pickers (cascading category/sub-type/date), Status filter, Major pills, Search, Core columns | Physical filter, Minor/Broad/IWA/DWA columns |

Explorer pages auto-compute % Tasks Affected, Workers Affected, and Wages Affected columns on page load in **both** simple and advanced modes using their respective default datasets (Occupation Explorer: AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft on Average; WA Explorer: AEI Cumul. (Both) v4), freq method, all phys, auto-aug on. The pct columns are always visible in the table (showing "---" while loading). In advanced mode, users can still open the PctComputePanel to re-run with custom settings. The Reset button restores all controls to defaults (including geo→nat, physical→all, hidden columns→defaults) and re-runs auto-compute. The WA Explorer auto-compute populates pctAffectedMap from all three levels (GWA + IWA + DWA) so results persist across level switches.

---

## 6. Comparison Model

The Occupation Categories and Work Activities pages use a **two-group (A/B) comparison design**. Each group has its own fully independent configuration — datasets, method, geography, aggregation, filters, and sort.

This exists because the most informative way to use this dashboard is to compare configurations against each other:
- **Different datasets** — "What does AEI see vs. what MCP sees?"
- **Different methods** — "How does frequency-based exposure compare to importance-weighted?"
- **Different filters** — "All tasks vs. non-physical tasks only"
- **Different geographies** — "National impact vs. Utah-specific impact"
- **Different aggregation levels** — "Major category view vs. individual occupations"

Tooltips on each bar show the delta versus the same category in the other group, making cross-group comparison immediate. The "Sync B → A" button enables a quick workflow where you set up one configuration, copy it, then change a single variable to isolate its effect.

---

## 7. Known Limitations & Scope Boundaries

**What the dashboard does NOT do:**
- **Predict job loss or replacement.** The metrics show task-level exposure overlap with AI capability, not employment forecasts. A high % Tasks Affected does not mean those workers will lose their jobs.
- **Capture all AI capabilities.** The AI scoring sources measure what current systems (Claude, MCP tools, Microsoft Copilot) can do as of their snapshot dates. Capabilities not captured in these datasets are not reflected.
- **Provide real-time data.** All data is from past snapshots. AEI Conv. snapshot data spans Dec 2024–Nov 2025; AEI cumulative variants aggregate all interactions through each snapshot date; MCP Cumul. spans Apr 2025–Feb 2026; Microsoft is a single Sep 2024 snapshot. BLS employment/wage data is from 2024 OEWS.
- **Cover non-U.S. labor markets.** Employment and wage data cover U.S. national, all 50 states, D.C., and select territories. The occupational taxonomy (O*NET / SOC) is U.S.-specific.

**Edge cases and caveats:**
- **AEI and MCP/Microsoft use different task baselines** for work activity analysis (O*NET 2015 vs. 2025), so they cannot be meaningfully combined in the same work activity group. The UI enforces this separation.
- **AEI data requires a crosswalk** from 2010 SOC to 2019 SOC codes. When an old occupation maps to multiple new ones, task scores are split proportionally. This introduces some approximation.
- **Explorer scores are computed across selected AI sources** using a fixed methodology (per-task averages/maximums across sources). The default is all 10 sources; in advanced mode, users can filter which sources contribute via the Sources selector.
- **The "Max" line mode in Trends is a cumulative running maximum** — it never decreases. This is by design (it shows the historical peak capability observed), but users should understand it is not a point-in-time measurement.
- **Physical task classification** is binary (physical or not). Some tasks have ambiguous physicality, and the classification comes from an LLM classification prompt from Microsoft's research.
