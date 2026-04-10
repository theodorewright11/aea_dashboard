# METHODOLOGY.md — AEA Dashboard

Compact reference for every number shown on the dashboard or produced by the `analysis/` system. Paired with [PRD.md](PRD.md) (what the product does), [ARCHITECTURE.md](ARCHITECTURE.md) (how it's built), and [analysis/ANALYSIS_PRD.md](analysis/ANALYSIS_PRD.md) (the research questions).

Equations are tagged (e.g. **E2.3**) so Part 3 can reference them without repeating the math. Fields in `code font` are actual column names in the final CSVs.

---

## Part 1 — Base Inputs

Every number on the dashboard ultimately resolves to one of the raw fields in `data/final_*.csv`. This part documents what each field is, its range, and how the pipeline (`aea_data_pipeline`) constructed it from source data.

### 1.1 Taxonomy Fields

| Field | Source | Notes |
|-------|--------|-------|
| `task`, `task_normalized` | O*NET task statements (v20.1 for 2015 ECO / AEI; v30.1 for 2025 ECO / MCP, MS, ECO) | `task_normalized` = lowercase + punctuation stripped + whitespace collapsed. Used as the universal join key across datasets. |
| `title` | O*NET occupation title (2010 SOC) | AEI datasets only |
| `title_current` | O*NET occupation title (2019 SOC) | MCP, Microsoft, ECO 2025 |
| `soc_code_2010`, `soc_code_2019_full` | 6-digit SOC codes | |
| `major_occ_category`, `minor_occ_category`, `broad_occ` | `soc_structure_2019.csv` | 23 major groups, joined on first 2/4/5 digits of SOC. A handful of anomalous codes are hard-patched (e.g. `15-1200 → 15-1000`). |
| `dwa_title`, `iwa_title`, `gwa_title` | O*NET `tasks_dwa_iwa_gwa_v{20.1,30.1}.csv` | A task can map to multiple DWAs. |
| `physical` (bool) | Microsoft physical-task classification, with DWA majority-rule imputation for unmapped tasks | Binary. Used by the physical-task filter. |
| `job_zone` (1–5) | O*NET `job_zones_v30.1.csv` | ECO 2025 only. 1 = little prep, 5 = extensive. |
| `dws_star_rating` (1–5) | Utah DWS outlook ratings | ECO 2025 only. Based on Utah projected openings (90%), growth rate (10%), and median wages. 5 = strongest outlook + high wages; 4 = good outlook + relatively high wages; 3 = moderate-to-strong outlook + low-to-moderate wages; 2 = high wages + limited outlook; 1 = low wages + strong outlook; 0 = limited outlook + low wages. Not a linear scale — 1 and 2 represent different tradeoffs, not ordered severity. Only occupations with ≥ 100 base employment are rated. Flag in risk scoring uses `{2, 3}` as at-risk. |
| `task_prop` | Computed in pipeline | ECO 2025 only. $\text{task\_prop} = n^{2015}_{\text{tasks}} / n^{2025}_{\text{tasks}}$ per occupation (2015 tasks mapped via SOC crosswalk). Used by the backend to deflate AEI task weights during the 2010→2019 crosswalk (§2.2). Clipped to $\geq 1$. |

### 1.2 O*NET Survey Measures: `freq_mean`, `importance`, `relevance`

Sourced from O*NET task ratings files (`task_ratings_v30.1.csv`, `task_ratings_may_2025.csv`, `task_ratings_oct_2015.csv`).

**Frequency conversion (E1.2.1).** O*NET reports frequency as a 7-bin distribution. The pipeline converts bin counts to a single `freq_mean` (expected tasks/day) using fixed weights:

$$
w_{\text{freq}} = \begin{cases}
1/260 & \text{bin 1 (yearly or less)} \\
4/260 & \text{bin 2} \\
24/260 & \text{bin 3} \\
104/260 & \text{bin 4} \\
1 & \text{bin 5 (once a day)} \\
3 & \text{bin 6} \\
8 & \text{bin 7 (multiple times per hour)}
\end{cases}
$$

$$
\text{freq\_mean} = \sum_{b=1}^{7} w_b \cdot p_b
$$

where $p_b$ is the survey share in bin $b$. Range: $\approx 0$–$8$.

| Field | Scale | What it is |
|-------|-------|-----------|
| `freq_mean` | ≈ 0–8 | Expected times per day this task is performed |
| `importance` | 1–5 | How important this task is to the occupation |
| `relevance` | 0–100 | % of respondents who consider this task relevant |

**Imputation chain (E1.2.2).** For missing `freq_mean`/`importance`/`relevance`, the pipeline walks an 8-level fallback. Minimum 5 values at each level before it can be used:

1. Direct `(title, task)` match
2. Task-only average (across all occs sharing the task)
3. Occupation average (across all tasks in the occ)
4. DWA average
5. IWA average
6. GWA average
7. Major occupation category average
8. Global mean

**Imputation penalty (E1.2.3).** If an occupation has more than 50% of its tasks imputed *below* the occupation level (levels 4–8), those imputed `freq_mean` values are halved:

$$
\text{freq\_mean}_{\text{imputed}} \;\leftarrow\; \tfrac{1}{2}\,\text{freq\_mean}_{\text{imputed}}
\quad \text{if} \quad \frac{n_{\text{imputed, below-occ}}}{n_{\text{total tasks in occ}}} > 0.5
$$

### 1.3 AI Scoring Fields: `auto_aug_mean`, `pct_normalized`

Both fields are **already averaged and normalized** in the final CSVs. ECO 2015/2025 files always have them null — values must come from an AI dataset.

| Field | Scale | Interpretation |
|-------|-------|---------------|
| `auto_aug_mean` | 0–5 | Automatability/augmentation rating (how much AI can do this task). |
| `pct_normalized` | Percent (0–100, typically < 1) | Share of AI conversations involving this task. **Already in percent form** (0.4 means 0.4%, not 40%). |

Four separate construction paths:

#### 1.3.1 AEI Conversation & AEI API (raw source: Anthropic Economic Index)

**`pct_normalized`** (`pct_to_onet_tasks()`):
- **v1–v2:** Loads `task_pct_v{1,2}.csv` (direct task-percentage mappings) and merges with O*NET v20.1 task statements on normalized task text.
- **v3+ and AEI API:** Filters raw AEI data for `GLOBAL/onet_task` entries and extracts percentage values.
- Counts `n_occurrences` per task (one task string can map to multiple occupations). Divides the raw pct by `n_occurrences` and then **normalizes globally to sum to 100**.

**`auto_aug_mean`**:
- **v2+:** Loads `automation_vs_augmentation_by_task_*.csv` from Anthropic's data release. Standardized across versions into a single 0–5 scale.
- **v1:** No auto/aug data available; column stays null. When computing `task_comp` (§2.1), missing `auto_aug_mean` contributes 0 under the auto-aug multiplier.

#### 1.3.2 MCP (Model Context Protocol servers)

Pipeline lives in the `mcp_classification_final` project. Classifies ~9,000+ MCP servers scraped from mcp.so against the O*NET occupational framework.

**Pipeline (E1.3.2):**
1. **Embed**: Voyage-4-large embeddings (1024-dim) of MCP description and all 2,083 O*NET DWAs.
2. **Retrieve top-80** DWAs per MCP by cosine similarity.
3. **Select DWAs** (GPT-4.1): picks up to 15 DWAs whose tasks the MCP could plausibly automate.
4. **Rate tasks** (GPT-4.1): per O*NET task under each selected DWA, rates 1–5:

   | Rating | Automation Coverage |
   |--------|---------------------|
   | 1 | 0–10%, no meaningful automation |
   | 2 | 10–30%, minimal support |
   | 3 | 30–60%, partial automation |
   | 4 | 60–90%, substantial automation |
   | 5 | 90–100%, near-full automation |

5. **Aggregate per task** across all MCPs that rated it: `mean_rating` (initial `auto_aug_mean`), `median`, `max`, `min`, `p25`, `p75`. `n_ratings` is the count of MCPs that rated this task.

**Winsorization (E1.3.2b).** In the dashboard pipeline, MCP ratings are winsorized per task at the 75th percentile + 1.5 × IQR before the final scale-mapping, reducing influence of outlier LLM ratings.

**`pct_normalized` for MCP.** Derived from `n_ratings` (number of MCPs rating the task) — tasks rated by more servers get a higher share. Normalized globally to sum to 100.

#### 1.3.3 Microsoft

Source: `iwa_metrics.csv` from Microsoft Copilot research. Metrics are reported at the IWA level, not the task level.

**Fields per IWA:** `impact_scope_ai`, `impact_scope_user`, `share_ai`, `share_user`.

**Scope aggregation (E1.3.3a):**

$$
\text{impact\_scope\_avg}_{\text{iwa}} = \frac{\text{share\_ai}\cdot\text{impact\_scope\_ai} + \text{share\_user}\cdot\text{impact\_scope\_user}}{\text{share\_ai} + \text{share\_user}}
$$

**Task distribution (E1.3.3b).** Each IWA's share is redistributed across all `(task, occupation)` pairs that fall under it, proportional to task weight, and then renormalized so all `pct_normalized` values across the dataset sum to 100.

**Scale mapping (E1.3.3c).** `impact_scope_avg` is mapped through MCP-derived conditional distributions (binned by scope) to produce a comparable `auto_aug_mean` on the same 1–5 scale.

#### 1.3.4 ECO 2015 & ECO 2025 Baselines

`final_eco_2025.csv` and `final_eco_2015.csv` have `auto_aug_mean = NaN` and `pct_normalized = 0` by design. They provide only the task inventory + survey fields and serve as the **denominator** in every `pct_tasks_affected` calculation (§2.3).

### 1.4 Employment & Wages: `emp_tot_{geo}_2024`, `a_med_{geo}_2024`

Sourced from BLS OEWS 2024 national (`oews_national_2024.csv`) and state-level files (`oews_states_2024.csv`). 55 geographies total: `nat` + 50 states + DC + Guam + Puerto Rico + USVI.

**Decimal SOC adjustment (E1.4.1).** O*NET uses decimal SOC codes (e.g. `11-1011.00`, `11-1011.03`); BLS reports at 6-digit level. Without adjustment, emp would be counted once per decimal variant. The pipeline reallocates:

1. Group rows by 6-digit SOC code.
2. Use `master_pct_normalized` as the split key, with **square-root dampening** to reduce influence of extremes:

   $$
   \text{emp}_i \;=\; \text{emp}_{\text{SOC6}} \cdot \frac{\sqrt{\text{pct}_i}}{\sum_j \sqrt{\text{pct}_j}}
   $$

3. If all pct values in a group are 0, fall back to equal split across titles.

**National wage fallback chain (`add_nat_wage_2024`).** For each occupation, in order:
1. BLS detailed 6-digit SOC median wage.
2. BLS broad-category SOC median wage.
3. Scraped O*NET wages (`scraped_wage_data.csv`, Jan 2020), multiplied by inflation factor **1.24**.
4. Hourly-to-annual conversion where only hourly is available.

**State wage fallback chain.** Shorter (no broad-category fallback for states):
1. State OEWS detailed SOC.
2. Hourly-to-annual conversion.
3. National wage.

**Employment fallbacks.**
- National: detailed SOC → broad SOC ÷ `broad_counts` (number of detailed occs in the broad group).
- State: state detailed SOC → national emp × (state total / national total).

**Titles mapping to multiple 2019 SOC codes.** Wages are averaged; employment is divided by the duplicate count then summed.

### 1.5 Cumulative Dataset Construction

The pipeline builds seven **cumulative** dataset families by combining snapshot sources. Each version accumulates all interactions up to a given date. Output naming: `final_{bucket}_{end_date}.csv`.

| Bucket | Sources | Task Set | Versions |
|---|---|---|---|
| `all_confirmed_usage` | AEI Conv + AEI API + Microsoft | 2025 | 6 |
| `confirmed_human_usage` | AEI Conv + Microsoft | 2025 | 6 |
| `aei_all_usage` | AEI Conv + AEI API | 2015 | 5 |
| `aei_human_usage` | AEI Conv only | 2015 | 5 |
| `aei_agentic_usage` | AEI API only | 2015 | 3 |
| `all_agentic_usage` | MCP + AEI API | 2025 | 7 |
| `all_usage` | AEI Both + MCP + Microsoft | 2025 | 10 |

**2015 task set builds** (`build_cumulative_2015`, E1.5a). Merge key: `(title, task_normalized, dwa_title, iwa_title, gwa_title)`. For matched rows:

$$
\begin{aligned}
\text{auto\_aug\_mean} &\;\leftarrow\; \max \text{ across source versions} \\
\text{pct\_normalized} &\;\leftarrow\; \max \text{ across source versions} \\
\text{date} &\;\leftarrow\; \text{latest}
\end{aligned}
$$

No pct renormalization — values preserve the scale of whichever source was higher.

**2025 task set builds** (`build_cumulative_2025`, E1.5b). Same max/max/latest rule, but joined to an ECO 2025 **backbone** on `(title_current, task_normalized)`. AEI/API sources (2010 SOC) match their `title` against ECO 2025 `title_current` before combining (~74% of AEI pairs match). MCP/Microsoft match `title_current` directly.

The five **analysis configs** in [analysis/config.py](analysis/config.py) all point at these pre-built cumulative files, so analysis scripts never have to do their own combine.

| Config key | Underlying file |
|---|---|
| `all_confirmed` (primary) | `AEI Both + Micro 2026-02-12` (= `final_all_confirmed_usage_2026-02-12`) |
| `all_ceiling` | `All 2026-02-18` (= `final_all_usage_2026-02-18`) |
| `human_conversation` | `AEI Conv + Micro 2026-02-12` |
| `agentic_confirmed` | `AEI API 2026-02-12` (= `final_aei_agentic_usage_2026-02-12`) |
| `agentic_ceiling` | `MCP + API 2026-02-18` (= `final_all_agentic_usage_2026-02-18`) |

---

## Part 2 — Derived Metrics (Math)

Everything downstream of the raw CSVs. All computations live in [backend/compute.py](backend/compute.py) (dashboard) or [analysis/data/compute_ska.py](analysis/data/compute_ska.py) (SKA).

**Notation.**
- $T$ = set of tasks (each is a `(title, task_normalized)` pair after deduplication)
- $f_t, r_t, i_t, a_t, e_o, w_o$ = `freq_mean`, `relevance`, `importance`, `auto_aug_mean`, `emp_tot_{geo}_2024`, `a_med_{geo}_2024`
- Superscripts $\text{AI}$ and $\text{ECO}$ denote AI dataset vs. ECO baseline.

### 2.1 Task Completion Weight: `task_comp`

Two methods and an optional multiplier. Subscripts drop for readability.

**E2.1.1 — Time method** (`method = "freq"`, the default):
$$\text{task\_comp} = f$$

**E2.1.2 — Value method** (`method = "imp"`):
$$\text{task\_comp} = f \cdot r \cdot i$$

**E2.1.3 — Auto-aug multiplier** (when `use_auto_aug = True`):
$$\text{task\_comp} \;\leftarrow\; \text{task\_comp} \cdot \frac{a}{5}$$

The ECO baseline is always computed **without** the auto-aug multiplier; it represents the full task profile of the occupation. Tasks with missing `auto_aug_mean` contribute 0 when the multiplier is on.

### 2.2 AEI Crosswalk & Deflation (2010 → 2019 SOC)

AEI datasets are native 2010 SOC. They must be converted before joining to the ECO 2025 / BLS 2019 backbone. Pipeline in `compute_single_dataset()` when `is_aei=True`:

1. **Dedup** AEI data on `(title, task_normalized)` and compute `task_comp` (E2.1).
2. **Join** the crosswalk `data/2010_to_2019_soc_crosswalk.csv` on `soc_code_2010`.
3. **Compute split_count** = number of distinct 2019 titles per 2010 code.
4. **Divide** `task_comp` and `emp` by `split_count` (E2.2a):

   $$\text{task\_comp}' = \frac{\text{task\_comp}}{\text{split\_count}}, \quad e' = \frac{e}{\text{split\_count}}$$

5. **Group by** `(2019 title, task_normalized)`; sum the divided `task_comp'` and `e'`.
6. **Deflate by `task_prop`** (E2.2b) — accounts for 2015→2025 task set changes:

   $$\text{task\_comp} \;\leftarrow\; \frac{\text{task\_comp}}{\max(\text{task\_prop},\, 1)}$$

7. **Backfill** `broad_occ`, `minor_occ_category`, `major_occ_category` from ECO 2025 where missing.

### 2.3 Occupation-Level Metrics

**E2.3.1 — % Tasks Affected** (ratio-of-totals, **never** an average of per-task percents):

$$
\text{pct\_tasks\_affected}_o \;=\; \frac{\sum_{t \in o} \text{task\_comp}^{\text{AI}}_t}{\sum_{t \in o} \text{task\_comp}^{\text{ECO}}_t} \times 100
$$

Clipped to $[0, 100]$. When an AEI task isn't in the ECO baseline, the AI numerator contributes but the ECO denominator doesn't change — this is why deflation (E2.2b) is needed.

**E2.3.2 — Workers Affected:**
$$
\text{workers\_affected}_o \;=\; \frac{\text{pct\_tasks\_affected}_o}{100} \cdot e_o
$$

**E2.3.3 — Wages Affected:**
$$
\text{wages\_affected}_o \;=\; \frac{\text{pct\_tasks\_affected}_o}{100} \cdot e_o \cdot w_o
$$

### 2.4 Group-Level Aggregation

For `agg_level ∈ {major, minor, broad}`:

**E2.4.1 — `pct_tasks_affected`** is **recomputed** at the group level as a ratio-of-totals, **not** averaged from occ-level pcts:

$$
\text{pct\_tasks\_affected}_G \;=\; \frac{\sum_{o \in G} \sum_{t \in o} \text{task\_comp}^{\text{AI}}_t}{\sum_{o \in G} \sum_{t \in o} \text{task\_comp}^{\text{ECO}}_t} \times 100
$$

**E2.4.2 — Workers / Wages Affected** are **summed** from occupation-level values:

$$
\text{workers\_affected}_G = \sum_{o \in G} \text{workers\_affected}_o, \quad \text{wages\_affected}_G = \sum_{o \in G} \text{wages\_affected}_o
$$

### 2.5 Work Activity Metrics (GWA / IWA / DWA)

A task can belong to multiple DWAs; each gets its full allocation (not double-counting — different aspects of the work).

**E2.5.1 — Weighted emp allocation per task within an occupation.** Previously an equal split; now weighted by survey effort:

| Method | weight per task |
|---|---|
| Time (`freq`) | $\omega_t = f_t$ |
| Value (`imp`) | $\omega_t = f_t \cdot r_t \cdot i_t$ |

$$
e^{\text{alloc}}_{t,o} \;=\; \frac{\omega_t}{\sum_{t' \in o} \omega_{t'}} \cdot e_o
$$

Backend pre-computes both variants (`emp_freq`, `emp_value`, `wage_freq`, `wage_value`) so the frontend can toggle without a refetch.

**E2.5.2 — Per-task worker/wage contribution:**

$$
w^{\text{contrib}}_{t,o} = \frac{\text{task\_comp}^{\text{AI}}_{t,o}}{\text{task\_comp}^{\text{ECO}}_{t,o}} \cdot e^{\text{alloc}}_{t,o}, \quad \$^{\text{contrib}}_{t,o} = w^{\text{contrib}}_{t,o} \cdot w_o
$$

**E2.5.3 — Activity-level rollup** (A = GWA, IWA, or DWA):

$$
\text{workers\_affected}_A = \sum_{t \in A} w^{\text{contrib}}_t, \quad \text{pct\_tasks\_affected}_A = \frac{\sum_{t \in A} \text{task\_comp}^{\text{AI}}_t}{\sum_{t \in A} \text{task\_comp}^{\text{ECO}}_t} \times 100
$$

**Baseline split.** AEI datasets must use `eco_2015` (2010 SOC native); MCP/Microsoft must use `eco_2025`. These cannot be mixed in the same activity group.

### 2.6 Multi-Dataset Combination

When multiple datasets are selected (e.g. `AEI Conv. v4 + MCP Cumul. v4 + Microsoft`), results are computed independently for each dataset then combined via `combine_results()`:

1. Rename metric columns with suffixes `_0`, `_1`, ...
2. Outer-join on the group column (fills missing with 0).
3. Apply a row-wise reducer:

**E2.6.1 — Average combine:**
$$
\text{metric}_G = \operatorname*{mean}_{d \in D}\left(\text{metric}_{G,d}\right)
$$

**E2.6.2 — Max combine:**
$$
\text{metric}_G = \operatorname*{max}_{d \in D}\left(\text{metric}_{G,d}\right)
$$

Applied independently to `pct_tasks_affected`, `workers_affected`, `wages_affected`.

### 2.7 Rank Columns

Computed **before** top-N filtering so rank is always relative to the full economy.

$$
\text{rank\_workers}_G = \text{rank}_{\text{desc}}(\text{workers\_affected}_G),\quad \text{rank\_wages}_G,\; \text{rank\_pct}_G \text{ analogously}
$$

Economy totals: $\text{total\_emp} = \sum_G \text{workers\_affected}_G$, $\text{total\_wages} = \sum_G \text{wages\_affected}_G$.

### 2.8 Explorer Metrics (`_compute_task_metrics`)

These are the pre-computed columns in the Occupation Explorer and Work Activities Explorer tables. They read from the `explorer task lookup`, which is a `{task_normalized → {source → (auto_aug, pct_norm)}}` dict built over all 10 sources.

For a set $T$ of `task_normalized` values and a set $S$ of selected sources:

**E2.8.1 — Per-task reductions across sources:**

$$
\bar{a}_t = \operatorname*{mean}_{s \in S,\, a_{t,s} \neq \text{null}} a_{t,s}, \quad a^{\max}_t = \operatorname*{max}_{s \in S} a_{t,s}
$$
$$
\bar{p}_t = \operatorname*{mean}_{s \in S,\, p_{t,s} \neq \text{null}} p_{t,s}, \quad p^{\max}_t = \operatorname*{max}_{s \in S} p_{t,s}
$$

**E2.8.2 — Group-level auto-aug metrics:**

| Column | Formula |
|---|---|
| `auto_avg_with_vals` | $\operatorname{mean}_{t \in T,\, \bar{a}_t \neq \text{null}}\; \bar{a}_t$ |
| `auto_max_with_vals` | $\operatorname{mean}_{t \in T,\, a^{\max}_t \neq \text{null}}\; a^{\max}_t$ |
| `auto_avg_all` | $\operatorname{mean}_{t \in T}\; (\bar{a}_t \text{ or } 0)$ |
| `auto_max_all` | $\operatorname{mean}_{t \in T}\; (a^{\max}_t \text{ or } 0)$ |

**E2.8.3 — Group-level pct metrics** use the same four-variant pattern on $\bar{p}_t$ and $p^{\max}_t$.

**E2.8.4 — Sum-of-pct columns:**
$$
\text{sum\_pct\_avg} = \sum_{t \in T,\, \bar{p}_t \neq \text{null}} \bar{p}_t, \quad \text{sum\_pct\_max} = \sum_{t \in T,\, p^{\max}_t \neq \text{null}} p^{\max}_t
$$

**Group-level important rule.** For major/minor/broad/GWA/IWA/DWA rows, $T$ is the **union of unique `task_normalized` values across all occupations/activities in the group** — never an average of child-group metrics. This is why these explorer metrics differ from the chart-page metrics (§2.3–2.5).

### 2.9 Explorer Emp/Wage Allocation (Task-Level Flat Table)

Used by `get_all_tasks()` (the "unique tasks" flat view in explorer):

**E2.9.1 — Equal split (simplified):**
$$
e^{\text{contrib}}_{t,o} = \frac{e_o}{n^{\text{unique}}_{\text{tasks in } o}}, \quad e_t = \sum_o e^{\text{contrib}}_{t,o}
$$

**E2.9.2 — Employment-weighted wage average** across occupations sharing a task:
$$
w_t = \frac{\sum_o e^{\text{contrib}}_{t,o} \cdot w_o}{\sum_o e^{\text{contrib}}_{t,o}}
$$

`get_all_eco_task_rows()` (the full ~23,850-row task view) uses the **weighted** allocation from E2.5.1 instead (`emp_freq` / `emp_value`) so it matches WA explorer numbers.

### 2.10 Task Changes Comparison

Compares two datasets at the task level. Per-row status:

| Status | Condition |
|---|---|
| **New** | row in "to" only AND `(task, occ)` exists in "from" dataset's eco baseline |
| **Removed** | row in "from" only AND `(task, occ)` exists in "to" dataset's eco baseline |
| **Changed** | in both, `auto_aug_mean` differs (null-vs-value counts as differing) |
| **Unchanged** | in both, same `auto_aug_mean` |
| **Not in baseline** | `(task, occ)` doesn't exist in the other dataset's eco baseline (cross-family only) |

**Deltas (E2.10.1):** $\Delta a = a^{\text{to}} - a^{\text{from}}$, $\Delta p = p^{\text{to}} - p^{\text{from}}$. Null if either side is null.

### 2.11 Trends & Cumulative Max

**Time series.** For each sub_type series key (e.g. `AEI Both + Micro`), the backend runs `compute_single_dataset()` for every dataset version in the series and records `date`.

**E2.11.1 — Cumulative-max line mode** (frontend):
$$
y^{\text{cum-max}}_T = \max_{t \leq T} y_t
$$
The line never decreases. Used for "peak capability observed to date" framing.

**E2.11.2 — Delta from first to last** (used by the Sort-by-Increase option):
$$
\Delta_{\text{abs}} = y_{T_{\text{last}}} - y_{T_{\text{first}}}, \quad \Delta_{\text{pct}} = \frac{y_{T_{\text{last}}} - y_{T_{\text{first}}}}{y_{T_{\text{first}}}} \cdot 100
$$

### 2.12 SKA Gap Formula (Analysis)

Skills / Abilities / Knowledge gap between AI capability and individual occupation requirements. Used by `worker_resilience/`, `job_risk_scoring/`, and several other analyses. Source: [analysis/data/compute_ska.py](analysis/data/compute_ska.py).

**Input:** `pct_tasks_affected` Series (title_current → 0–100) for one analysis config.

**Constants:** `IMPORTANCE_THRESHOLD = 3.0`, `AI_PERCENTILE = 95`.

Per O*NET element (skills / abilities / knowledge), with per-occ values $\text{imp}_{o,e}, \text{lvl}_{o,e}$ and a filter of `importance ≥ 3` applied **per row** (not globally — a skill unimportant in one occ can still be valid in another):

**E2.12.1 — Occupation element score:**
$$
\text{occ\_score}_{o,e} = \text{imp}_{o,e} \cdot \text{lvl}_{o,e}
$$

**E2.12.2 — AI product (weighted by exposure):**
$$
\text{ai\_product}_{o,e} = \frac{\text{pct\_tasks\_affected}_o}{100} \cdot \text{imp}_{o,e} \cdot \text{lvl}_{o,e}
$$

**E2.12.3 — AI capability per element** (95th percentile across all occs):
$$
\text{ai\_score}_e = Q_{0.95}\!\left(\{\text{ai\_product}_{o,e} : o \in \mathcal{O}\}\right)
$$

**E2.12.4 — Eco baseline** (reference only, not used in the gap):
$$
\text{eco\_score}_e = \operatorname*{mean}_{o \in \mathcal{O}} \text{occ\_score}_{o,e}
$$

**E2.12.5 — Per-(occ, element) gap:**
$$
\text{gap}_{o,e} = \text{ai\_score}_e - \text{occ\_score}_{o,e}
$$

- $\text{gap} > 0$: AI exceeds this occupation's need for this element → leverage AI here.
- $\text{gap} < 0$: Human advantage → focus training here.

**E2.12.5b — Per-(occ, element) percentage framing:**
$$
\text{ai\_pct\_occ}_{o,e} = \frac{\text{ai\_score}_e}{\text{occ\_score}_{o,e}} \times 100
$$

Above 100% = AI leads; below 100% = human advantage. No cap applied.

**E2.12.6 — Per-occupation summary:**
$$
\text{skills\_gap}_o = \operatorname*{mean}_{e \in \text{skills}} \text{gap}_{o,e}
$$

Same for `abilities_gap` and `knowledge_gap`, then:

$$
\text{overall\_gap}_o = \frac{\text{skills\_gap}_o + \text{abilities\_gap}_o + \text{knowledge\_gap}_o}{3}
$$

**E2.12.6b — Per-occupation percentage summary (ratio-of-sums):**
$$
\text{overall\_pct}_o = \frac{\sum_{e : \text{imp}_{o,e} \geq 3} \text{ai\_score}_e}{\sum_{e : \text{imp}_{o,e} \geq 3} \text{occ\_score}_{o,e}} \times 100
$$

This is ratio-of-sums (consistent with `pct_tasks_affected`), not mean-of-ratios. Above 100% = AI leads. Legacy `overall_gap` (mean of per-type mean gaps, E2.12.6) is still emitted for backward compatibility.

**Per-type percentage variants:** `skills_pct`, `abilities_pct`, `knowledge_pct` follow the same ratio-of-sums pattern restricted to elements of that type.

**`eco_baseline_p95` (E2.12.4b).** Alongside the existing `eco_baseline` (mean, E2.12.4), a 95th-percentile `occ_score` per element is now emitted for the "top-practitioner" baseline in `skills_landscape` charts:
$$
\text{eco\_baseline\_p95}_e = Q_{0.95}\!\left(\{\text{occ\_score}_{o,e} : o \in \mathcal{O}\}\right)
$$

*Locked-in spec note:* The 95th percentile is defended via the `ai_capability_method_comparison.ipynb` notebook (demonstrated capability floor of ~46 occupations, outlier stability, bootstrap robustness).

**Worker resilience ranking.** Sort by `gap` ascending (most negative = largest human advantage = best training target).

**SKA trend (E2.12.7).** Recompute at first and last date of `ANALYSIS_CONFIG_SERIES[config_key]` only, then:
$$
\Delta\text{gap}_o = \text{overall\_gap}^{\text{last}}_o - \text{overall\_gap}^{\text{first}}_o
$$

### 2.13 Job Risk Scoring

From `questions/job_exposure/job_risk_scoring/`. Weighted 8-factor composite, computed per occupation against the primary config (`all_confirmed`).

**E2.13.1 — Flags and weights:**

| Flag | Weight | Condition |
|---|---|---|
| 1 | 2 | `pct_tasks_affected > 50%` (absolute threshold, not median) |
| 2 | 2 | `overall_pct > median(overall_pct)` (SKA percentage framing, ratio-of-sums, E2.12.6b) |
| 3 | 1 | `pct_delta > 0` AND `pct_delta > median(pct_delta)` (trend weight reduced from 2→1) |
| 4 | 1 | `ska_delta > 0` AND `ska_delta > median(ska_delta)` (trend weight reduced from 2→1) |
| 5 | 1 | `job_zone ∈ {1, 2, 3}` |
| 6 | 1 | `dws_star_rating ∈ {2, 3}` (note: 1 = good outlook + high wages, **not** at risk) |
| 7 | 1 | `n_software > median(n_software)` (from `tech_skills_simple.csv`) |
| 8 (NEW) | 1 | `auto_avg_with_vals > median(auto_avg_with_vals)` |

**E2.13.2 — Weighted score:**
$$
S_o = 2(F_{1,o} + F_{2,o}) + 1(F_{3,o} + F_{4,o} + F_{5,o} + F_{6,o} + F_{7,o} + F_{8,o})
$$

Maximum possible $S = 10$.

**E2.13.3 — Exposure gate (4 tiers):**
$$
\text{tier}_o = \begin{cases}
\text{Low} & S_o \in [0, 2] \\
\text{Mod-Low} & S_o \in [3, 4] \\
\text{Mod-High} & S_o \in [5, 7] \\
\text{High} & S_o \in [8, 10] \text{ AND } \text{pct\_tasks\_affected}_o \geq 33 \\
\text{Mod-High} & S_o \in [8, 10] \text{ AND } \text{pct\_tasks\_affected}_o < 33 \text{ (exposure-gated)}
\end{cases}
$$

Changes from prior scheme: 7→8 flags, trend weights 2→1, flag 1 from median→absolute 50%, flag 2 from raw `overall_gap` to `overall_pct`, 3→4 tiers.

**`n_software` field (E2.13.4).** From `analysis/data/tech_skills_simple.csv`, generated by `compute_tech_skills.py`:
$$
\text{n\_software}_o = \text{count of rows in } \texttt{technology\_skills\_v30.1.csv} \text{ with this occupation}
$$

This is a **per-occupation** collapse of the same source file that §2.18 uses for the tech category footprint. Risk scoring only needs the row count per occupation ("does this occ touch a lot of software?"); skills_landscape instead keeps the per-category dimension to ask "which categories dominate the exposed economy?". Different pivots, same CSV.

### 2.14 Pivot Distance (Analysis)

From `questions/job_exposure/pivot_distance/`. Measures the reskilling cost for a worker in a high-risk occupation to cross over to a low-risk occupation in the **same job zone**.

**Not a distance metric — L1 rectified distance.** This is a **rectified element-wise gap sum** (L1 rectified distance) — not cosine, Euclidean, projection, or anything symmetric. Only the elements where the low-risk group scores *above* the high-risk group contribute (those are the skills the high-risk worker would need to learn); elements where the high-risk group is already above are dropped from the sum. The sum-of-positive-differences formula is NOT vector projection.

**Elements used.** Skills + Knowledge only. **Abilities are excluded** as they are less trainable in the short term.

**Inputs per job zone** $z \in \{1,\dots,5\}$, from `job_risk_scoring/results/pivot_distance_inputs.csv`:
- $H_z$ — top 10 highest-risk occupations in zone $z$ (or $\min(10, n)$ if fewer exist, per ANALYSIS_ARCHITECTURE.md pitfall).
- $L_z$ — bottom 10 lowest-risk occupations in zone $z$.

**E2.14.1 — Group-average element score** (per SKA element $e$, filter `importance ≥ 3` per (occ, element)):

$$
\bar{s}^{H}_{z,e} = \operatorname*{mean}_{o \in H_z} \left(\text{imp}_{o,e} \cdot \text{lvl}_{o,e}\right), \quad \bar{s}^{L}_{z,e} = \operatorname*{mean}_{o \in L_z} \left(\text{imp}_{o,e} \cdot \text{lvl}_{o,e}\right)
$$

**E2.14.2 — Per-element pivot cost** (rectified positive gap):

$$
\text{cost}_{z, e} = \max\!\left(0,\; \bar{s}^{L}_{z,e} - \bar{s}^{H}_{z,e}\right)
$$

**E2.14.3 — Zone total pivot cost:**

$$
\text{total\_pivot\_cost}_z = \sum_{e \in \text{skills} \cup \text{knowledge}} \text{cost}_{z, e}
$$

**E2.14.4 — "AI can help" flag** per element: true iff the element's AI capability score (E2.12.3 from compute_ska, computed on the low-risk group's pct) exceeds the high-risk group's score:

$$
\text{ai\_can\_help}_{z,e} \;=\; \mathbf{1}\!\left[\text{cost}_{z,e} > 0 \;\wedge\; \text{ai\_score}_e > \bar{s}^{H}_{z,e}\right]
$$

**E2.14.3b — Pct new ground:**
$$
\text{pct\_new\_ground}_z = \frac{\text{total\_pivot\_cost}_z}{\sum_{e : \text{cost}_{z,e} > 0} \bar{s}^{L}_{z,e}} \times 100
$$

Reads as "X% of the destination job's skill mass in those areas is new territory."

Both absolute pivot cost and `pct_new_ground` are reported per zone, with primary ranking by absolute mass. A calibration reference (theoretical max, empirical mean/median/std/max of per-occ skill+knowledge mass) is included in chart subtitles.

**Tiebreaker for zone bucket selection.** When selecting the top/bottom 10 occupations per zone: `pct_tasks_affected` descending for high-risk, ascending for low-risk.

**Ceiling comparison.** The same pipeline is run a second time with `pct = all_ceiling` instead of `all_confirmed`, producing `ceiling_pivot_cost_z` and `cost_delta_ceiling_z = ceiling_pivot_cost_z − total_pivot_cost_z`.

### 2.15 Clustering (State Clusters)

From `questions/state_clusters/`. Standard K-means on state feature vectors (sector shares, risk-tier shares, GWA shares, etc.).

**E2.15.1 — Adjusted Rand Index** for comparing two clustering schemes $U$ and $V$ on the same set of states:

$$
\text{ARI}(U, V) = \frac{\sum_{ij} \binom{n_{ij}}{2} - \left[\sum_i \binom{a_i}{2} \sum_j \binom{b_j}{2}\right] / \binom{n}{2}}{\frac{1}{2}\left[\sum_i \binom{a_i}{2} + \sum_j \binom{b_j}{2}\right] - \left[\sum_i \binom{a_i}{2} \sum_j \binom{b_j}{2}\right] / \binom{n}{2}}
$$

$\text{ARI} = 1$ → identical clustering; $\text{ARI} \approx 0$ → random agreement.

**E2.15.2 — State stability score:** for each state, the share of other states with which it is grouped under at least 3 of the 5 clustering schemes.

### 2.16 Trajectory Classification (Time Trends)

From `questions/time_trends/trajectory_shapes/`. Each occupation's time series of `pct_tasks_affected` is bucketed into one of six shapes based on:
- $\Delta_{\text{abs}}$ (E2.11.2) — total pp gain
- The date of the largest single inter-version jump
- Monotonicity (whether the series ever retreated)

Thresholds are set empirically; see `trajectory_shapes/run.py` for the exact cutoffs. Categories: *early-takeoff, late-takeoff, steady, plateaued, laggard, volatile*.

### 2.17 Adoption Gap (Potential Growth)

From `questions/potential_growth/adoption_gap/`.

**E2.17.1 — Per-occupation adoption gap (pp):**
$$
\text{gap}_o = \text{pct}^{\text{ceiling}}_o - \text{pct}^{\text{confirmed}}_o
$$
with `all_ceiling` and `all_confirmed` as the two configs.

**E2.17.2 — Wage gap ($):**
$$
\$\text{gap}_o = \frac{\text{gap}_o}{100} \cdot e_o \cdot w_o
$$

### 2.18 Tech Category Exposure (Skills Landscape)

From `questions/economic_footprint/skills_landscape/`. A completely separate computation from SKA (§2.12) and from `n_software` (§2.13.4), even though all three pull from the same `technology_skills_v30.1.csv` file.

**Input.** `technology_skills_v30.1.csv` — one row per `(Title, Commodity Title)` pairing, where `Title` is an O*NET occupation and `Commodity Title` is one of ~127 technology categories the occupation uses. Let $\mathcal{T}$ be this set of (occ, category) pairs.

**Join.** Each row is enriched with:
- `emp_o` — national employment for that occupation (from `get_explorer_occupations()`, §1.4).
- `pct_o` — `pct_tasks_affected` for that occupation from the primary config `all_confirmed` (via `get_pct_tasks_affected()`, which goes through E2.3.1).
- `wage_o` — median annual wage for that occupation (§1.4).
- `major_o` — the occupation's major SOC category.
- `n_commodities_o` — number of distinct commodity titles listed for the occupation.

Three charts plus a heatmap, each answering a different question:

**E2.18.1 — Chart 1: Mean pct_tasks_affected per commodity.** Across all (occ, software) rows for commodity $c$:

$$
\text{mean\_pct}_c \;=\; \operatorname*{mean}_{o \,:\, (o,c) \in \mathcal{T}} \text{pct\_tasks\_affected}_o
$$

No employment weighting. Answers: "what % of this software's usage is AI-affected."

**E2.18.2 — Chart 2: Exposed workers per commodity.** For each commodity $c$:

$$
\text{exposed\_workers}_c \;=\; \sum_{o \,:\, (o,c) \in \mathcal{T}} \frac{\text{pct\_tasks\_affected}_o}{100} \cdot e_o
$$

Workers in AI-affected use. No per-commodity divisor needed (workers genuinely use multiple commodities). Label includes % of commodity users affected.

**E2.18.3 — Chart 3: Exposed wages per commodity.** For each commodity $c$:

$$
\text{exposed\_wages}_c \;=\; \sum_{o \,:\, (o,c) \in \mathcal{T}} \frac{\text{pct\_tasks\_affected}_o}{100} \cdot e_o \cdot \frac{w_o}{n_{\text{commodities}_o}}
$$

The $n_{\text{commodities}}$ divisor prevents wage double-counting across commodities within the same occupation. Label includes % of commodity wages affected.

**E2.18.4 — Heatmap: Per-sector tech penetration.** For each major SOC group $G$ and each top-25 category $c$:

$$
\text{pct\_occs}_{G, c} \;=\; \frac{\left|\{o \in G : (o, c) \in \mathcal{T}\}\right|}{\left|\{o \in G : \exists c'\,(o, c') \in \mathcal{T}\}\right|} \times 100
$$

This is an **unweighted** share: the percent of occupations in sector $G$ (among those that appear at all in `technology_skills_v30.1.csv`) that list technology category $c$. Columns are now ordered by Chart 2 ranking (exposed workers, most → left). Cell value unchanged (% of occs in sector using the commodity).

---

## Part 3 — Reference Index

For every dashboard page and every analysis sub-question: which equations from Part 2 (and which raw inputs from Part 1) produce the numbers shown. This section does not repeat math — only points at named tags.

### 3.1 Dashboard Pages

#### 3.1.1 Occupation Explorer (`/explorer`)

Table rows at Major / Minor / Broad / Occupation / Task levels. Values shown per row:

| Column(s) | Equations |
|---|---|
| `emp`, `wage` (group levels = first/average of occ values; task level = raw occupation emp/wage for the row's occ) | §1.4, §1.4 fallback chains |
| `auto_avg/max_with_vals`, `auto_avg/max_all`, `pct_avg/max_*`, `sum_pct_*` | **E2.8.1–4** across selected sources |
| `% tasks affected` (via PctComputePanel) | **E2.3.1** or **E2.4.1** |
| `workers_affected` (via PctComputePanel) | **E2.3.2** then **E2.4.2** |
| `wages_affected` (via PctComputePanel) | **E2.3.3** then **E2.4.2** |
| Task-level drilldown source-breakdown AVG / MAX footer | **E2.8.1** |
| Job Outlook (Utah), Job Zone | §1.1 fields, averaged at group level |

AEI sources in the PctComputePanel trigger **E2.2** (crosswalk + deflation). Source selector gates which source keys $S$ appear in **E2.8.1**.

#### 3.1.2 Work Activities Explorer (`/wa-explorer`)

Same table structure as Occupation Explorer but organized GWA → IWA → DWA → Task.

| Column(s) | Equations |
|---|---|
| `emp`, `wage` per row | **E2.5.1** (weighted by Time/Value toggle) |
| Auto/pct metric columns | **E2.8.1–4** over all tasks in the activity |
| `% tasks affected`, `workers_affected`, `wages_affected` (via PctComputePanel) | **E2.5.3** |

#### 3.1.3 Occupation Categories (`/categories`)

Horizontal bar charts for the two groups × three metrics (Workers, Wages, % Tasks Affected). Per group:

| Element | Equations |
|---|---|
| Task weight | **E2.1.1–3** |
| AEI pre-processing | **E2.2** |
| Per-occupation pct / workers / wages | **E2.3.1–3** |
| Major / Minor / Broad rollup | **E2.4.1–2** |
| Multi-dataset combine | **E2.6.1** or **E2.6.2** |
| Rank labels in tooltips | §2.7 |
| Economy share in tooltips | $\text{workers\_affected}_G \,/\, \text{total\_emp}$ |
| Cross-group delta in tooltips | $(v_B - v_A)$ and $(v_B - v_A)/v_A \times 100$ |

#### 3.1.4 Work Activities (`/work-activities`)

Same as Occupation Categories but:

| Element | Equations |
|---|---|
| Emp allocation | **E2.5.1** |
| Per-task contribution | **E2.5.2** |
| Activity rollup | **E2.5.3** |
| Multi-dataset combine (within the AEI or MCP/MS family only) | **E2.6.1–2** |

The AEI-family vs MCP/MS-family split enforces the baseline rule from §2.5.

#### 3.1.5 Trends (`/trends`)

| Element | Equations |
|---|---|
| Data points per dataset version | **E2.3.1–3** → **E2.4.1–2** or **E2.5.3** for WA tab |
| "Average" line mode across selected datasets at each date | **E2.6.1** |
| "Max" line mode | **E2.11.1** (cumulative max) |
| Sort-by-Increase metric | **E2.11.2** |

#### 3.1.6 Task Changes Explorer (`/task-changes`)

| Element | Equations |
|---|---|
| Per-row `auto_aug`, `pct` for From/To | §1.3 raw fields (AEI averaged across 2010 SOC titles; MCP winsorized; MS scale-mapped) |
| AEI datasets preprocessed via crosswalk dedup | **E2.2** (steps 1–5) |
| Status assignment | §2.10 |
| Δ columns | **E2.10.1** |
| Source-breakdown drilldown AVG / MAX | **E2.8.1** |

#### 3.1.7 About Page

Displays every equation in §2.1–2.5 with human-readable labels. The source of truth for those displays is this document.

### 3.2 Analysis Buckets

#### 3.2.1 `job_exposure/`

All sub-questions use one or more of the five **ANALYSIS_CONFIGS** (§1.5) as the dataset input.

| Sub-folder | Inputs (Part 1) | Core math (Part 2) |
|---|---|---|
| `exposure_state/` | all 5 configs, `ANALYSIS_CONFIG_SERIES` for trends | **E2.3.1–3**, **E2.4.1–2** (major rollup), **E2.11.2** |
| `job_risk_scoring/` | `all_confirmed` primary; `tech_skills_simple.csv`; `job_zone`, `dws_star_rating` from §1.1 | **E2.12.1–7** (SKA + SKA trend), **E2.13.1–4** (8-flag composite, 4 tiers) |
| `worker_resilience/` | `all_confirmed`; SKA data | **E2.12.1–6**, **E2.12.5b**, **E2.12.6b** (percentage framing), sorted ascending by `gap` |
| `pivot_distance/` | `pivot_distance_inputs.csv` from `job_risk_scoring`; SKA (skills+knowledge only); `job_zone` | **E2.14.1–4**, **E2.14.3b** (pct new ground) (per zone, both `all_confirmed` and `all_ceiling`; L1 rectified distance, not projection) |
| `audience_framing/` | All outputs from the above; `OCCS_OF_INTEREST` | No new math — aggregates, overlaps, domain labels |
| `occs_of_interest/` | `OCCS_OF_INTEREST` from §1.5 refs | **E2.3.1–3** filtered to the 29 named titles |

#### 3.2.2 `work_activity_exposure/`

All sub-questions use `all_confirmed` primary, `all_ceiling` for confirmed/ceiling framing. Work activity metrics go through **E2.5.1–3**. Four of five configs use `is_aei=False` (eco_2025 baseline); `agentic_confirmed` uses `is_aei=True` (eco_2015 baseline, aei_group path).

| Sub-folder | Inputs | Core math |
|---|---|---|
| `exposure_state/` | all 5 configs, IWA/GWA/DWA levels | **E2.5.1–3**, **E2.11.2** for trends |
| `activity_robustness/` | `all_confirmed`, `all_ceiling` | **E2.5.3**; robustness tier = `pct_tasks_affected` cutoffs at 33% and 66%; ceiling gap = `pct^ceiling − pct^confirmed` |
| `education_lens/` | `all_confirmed`, SOC-level employment via **E2.5.1** | **E2.5.1–3**, tier-weighted worker rollups |
| `audience_framing/` | Aggregated outputs from the above | No new math |

#### 3.2.3 `potential_growth/`

Uses `all_confirmed` vs `all_ceiling`.

| Sub-folder | Core math |
|---|---|
| `adoption_gap/` | **E2.17.1** (per-occ and per-activity), **E2.4.1–2** / **E2.5.3** for rollup |
| `wage_potential/` | **E2.17.2**; top-quartile intersection on `wage` and `adoption_gap` |
| `automation_opportunity/` | **E2.12** (SKA gap, AI-leads quadrant Q1; quadrant split at 100% via percentage framing — natural threshold, not median), plus **E2.17.1** for the adoption gap axis, intersected with **E2.13** tiers for "transformation signal" |
| `audience_framing/` | No new math |

#### 3.2.4 `source_agreement/`

Compares four raw sources: Human Conv (`AEI Conv + Micro 2026-02-12`), Agentic (`AEI API 2026-02-12`), Microsoft, MCP Cumul. v4.

| Sub-folder | Inputs | Core math |
|---|---|---|
| `ranking_agreement/` | per-source `pct_tasks_affected` from **E2.3.1** | Spearman $\rho$ on per-source rankings at every agg level; cross-source confidence tier = rank in how many sources? |
| `score_distributions/` | per-source `auto_aug_mean` (§1.3) | Histograms + per-occ variance of `auto_aug_mean` across sources |
| `source_portraits/` | per-source ranks | Deviation-from-consensus per source × category |
| `marginal_contributions/` | stepwise combine | **E2.6.1** (Average combine), tier shifts across incremental layers |

#### 3.2.5 `agentic_usage/`

Uses three datasets: `agentic_confirmed` (AEI API 2026-02-12), MCP Cumul. v4 (MCP only), `agentic_ceiling` (MCP + API 2026-02-18).

| Sub-folder | Core math |
|---|---|
| `exposure_state/` | **E2.3.1–3**; tier distributions |
| `sector_footprint/` | **E2.4.1–2** |
| `work_activities/` | **E2.5.1–3** (AEI API → eco_2015 path; MCP → eco_2025 path — not combined) |
| `mcp_profile/` | **E2.8.1** (MCP-only source filter); ratio of MCP contribution to combined |
| `trends/` | **E2.11.2** over the agentic series |

#### 3.2.6 `economic_footprint/`

All five configs, primary = `all_confirmed`.

| Sub-folder | Core math |
|---|---|
| `sector_footprint/` | **E2.3.1–3** → **E2.4.1–2** at the major level |
| `skills_landscape/` | Two distinct parts. **SKA side:** **E2.12.3–4** at the economy level (AI-leads vs human-leads elements), **E2.12.5b** for percentage framing with both `eco_mean` (E2.12.4) and `eco_p95` (E2.12.4b) baselines, + **E2.12.6** averaged by major sector across **all five configs** for the major × config heatmap. **Tech side:** **E2.18** revised (3 charts + reordered heatmap): **E2.18.1** (mean pct per commodity), **E2.18.2** (exposed workers per commodity), **E2.18.3** (exposed wages per commodity), **E2.18.4** (per-sector penetration heatmap, columns ordered by Chart 2 ranking) (all using `all_confirmed`). |
| `job_structure/` | **E2.3.1–3** grouped by `job_zone` and `dws_star_rating` |
| `ai_modes/` | Agentic vs conversational comparison via two different configs (`agentic_confirmed` vs `human_conversation`); auto-aug histogram from §1.3 |
| `trends/` | **E2.11.2** per config |
| `state_profiles/` | **E2.3.1–3** per state (geo ∈ §1.4 55 options); k-means on sector shares (E2.15) |
| `work_activities/` | **E2.5.1–3** |

#### 3.2.7 `field_benchmarks/`

No new math — this bucket takes our **E2.3.1–3** outputs and compares them side-by-side with external benchmarks (Project Iceberg, Seampoint, Humlum & Vestergaard, Weidinger ChatGPT usage, Microsoft Copilot). All internal numbers flow through the same E2.3 → E2.4 / E2.5 pipeline.

#### 3.2.8 `state_clusters/`

Uses all five configs plus 55 geographies (§1.4).

| Sub-folder | Core math |
|---|---|
| `risk_profile/` | **E2.13** per state; k-means on risk-tier shares |
| `activity_signature/` | **E2.5.1–3** per state; k-means on GWA shares |
| `agentic_profile/` | ratio of (agentic_confirmed workers / all_confirmed workers) per sector; k-means |
| `adoption_gap/` | **E2.17.1** per sector × state; k-means on gap shares |
| `cluster_convergence/` | **E2.15.1** (ARI), **E2.15.2** (stability score) |

#### 3.2.9 `time_trends/`

Primary series: `all_confirmed` (6 dates). Ceiling: `all_ceiling` (10 dates).

| Sub-folder | Core math |
|---|---|
| `trajectory_shapes/` | **E2.11.2** + E2.16 classification |
| `tier_churn/` | Tier cutoffs on `pct_tasks_affected` at each date; transition matrix between consecutive dates |
| `confirmed_ceiling_convergence/` | $\text{ratio}(t) = \text{pct}^{\text{confirmed}}(t)\,/\,\text{pct}^{\text{ceiling}}(t)$, trend over $t$ |
| `wa_tipping_points/` | **E2.5.3** per IWA per date; threshold crossings at 10%, 33%, 66% |
| `occs_timeline/` | **E2.3.1–3** per date, filtered to `OCCS_OF_INTEREST` |

---

## Appendix A — Common Pitfalls When Reading Numbers

1. **`pct_tasks_affected` is always ratio-of-totals.** Never average per-occ pcts to get a group pct — re-derive from `task_comp` sums (§2.3, §2.4).
2. **`pct_normalized` is already in percent form.** 0.4 means 0.4%, **not** 40%.
3. **Explorer `auto_*` / `pct_*` columns ≠ chart-page metrics.** Explorer metrics pool unique task_norms across the group (§2.8); chart metrics flow through task_comp and weighted allocation (§2.3, §2.5).
4. **AEI datasets require crosswalk + deflation.** Skipping either produces inflated AI numerators (§2.2).
5. **DWS star rating 1 = good outlook.** Flag as at-risk only `{2, 3}` (§2.13).
6. **SKA importance filter is per-row.** Don't apply it globally — an element can be important in one occ and not another (§2.12).
7. **AEI vs MCP/MS cannot be combined at the WA level.** Different task baselines (eco_2015 vs eco_2025). The dashboard enforces this (§2.5).
8. **MCP ratings are winsorized.** At 75th percentile + 1.5×IQR before final aggregation (§1.3.2b).
9. **`task_prop` clipped to ≥ 1.** Deflation can only reduce AEI task_comp, never inflate it (§2.2b).
10. **Cumulative datasets preserve max, not sum.** `auto_aug_mean` and `pct_normalized` are taken as max across source versions, not added together (§1.5).

---

## Appendix B — Dataset-to-Equation Lookup

| Dataset family | Baseline | Crosswalk? | Equations hit on every compute |
|---|---|---|---|
| AEI Conv. (v1–v5), AEI API (v3–v5) | eco_2015 for WA; eco_2025 for occ after crosswalk | Yes (§2.2) | **E2.1**, **E2.2**, **E2.3 or E2.5**, **E2.4** |
| AEI Cumul. Conv. / API / Both | same as above | Yes | same as above |
| MCP Cumul. (v1–v4) | eco_2025 | No | **E2.1**, **E2.3 or E2.5**, **E2.4** |
| Microsoft | eco_2025 | No | same as MCP |
| All confirmed / All / MCP+API / etc. (pre-combined cumulative) | eco_2025 (or eco_2015 for AEI-only variants) | No — already crosswalked in the pipeline | **E2.1**, **E2.3 or E2.5**, **E2.4** |
