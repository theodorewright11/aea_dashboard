# ANALYSIS_ARCHITECTURE.md — Analysis System Architecture

Technical reference for the `analysis/` folder. Does not repeat information in the main `ARCHITECTURE.md`.

---

## Folder Structure

```
analysis/
├── ANALYSIS_CLAUDE.md       — Agent rules for analysis work
├── ANALYSIS_PRD.md          — Question catalog, audiences, five configs
├── ANALYSIS_ARCHITECTURE.md — This file
├── charts.md                — Dashboard reproduction guide for all committed figures (all buckets)
├── config.py                — Shared paths, ANALYSIS_CONFIGS, ANALYSIS_CONFIG_SERIES,
│                              OCCS_OF_INTEREST, get_pct_tasks_affected(), helpers
├── utils.py                 — Chart styling, PDF generation, save helpers
├── run_all.py               — Reference only (broken; old dataset names)
├── data/
│   ├── skills_v30.1.csv         — O*NET v30.1 skills (base file, do not delete)
│   ├── abilities_v30.1.csv      — O*NET v30.1 abilities (base file)
│   ├── knowledge_v30.1.csv      — O*NET v30.1 knowledge (base file)
│   ├── technology_skills_v30.1.csv — O*NET v30.1 tech skills (base file)
│   ├── tech_skills_simple.csv   — Static: soc_code, title, n_software (generated)
│   ├── compute_ska.py           — Real-time SKA gap computation module
│   ├── compute_tech_skills.py   — Generates tech_skills_simple.csv
│   └── old_scripts/             — Reference only (notebook + old ratio script)
├── questions/
│   ├── _template/
│   ├── economic_footprint/      — Active question bucket
│   │   ├── README.md
│   │   ├── economic_footprint_report.md
│   │   ├── sector_footprint/
│   │   ├── skills_landscape/
│   │   ├── job_structure/
│   │   ├── ai_modes/
│   │   ├── trends/
│   │   ├── state_profiles/
│   │   └── work_activities/
│   ├── job_exposure/            — Active question bucket
│   │   ├── README.md
│   │   ├── job_exposure_report.md
│   │   ├── exposure_state/
│   │   ├── job_risk_scoring/
│   │   ├── worker_resilience/
│   │   ├── pivot_distance/
│   │   ├── audience_framing/
│   │   └── occs_of_interest/
│   ├── work_activity_exposure/  — Active question bucket
│   │   ├── README.md
│   │   ├── work_activity_exposure_report.md
│   │   ├── exposure_state/
│   │   ├── activity_robustness/
│   │   ├── education_lens/
│   │   └── audience_framing/
│   ├── potential_growth/        — Active question bucket
│   │   ├── README.md
│   │   ├── potential_growth_report.md
│   │   ├── adoption_gap/
│   │   ├── wage_potential/
│   │   ├── automation_opportunity/
│   │   └── audience_framing/
│   ├── source_agreement/        — Active question bucket
│   │   ├── README.md
│   │   ├── source_agreement_report.md
│   │   ├── ranking_agreement/
│   │   ├── score_distributions/
│   │   ├── source_portraits/
│   │   └── marginal_contributions/
│   ├── agentic_usage/           — Active question bucket
│   │   ├── README.md
│   │   ├── agentic_usage_report.md
│   │   ├── exposure_state/
│   │   ├── sector_footprint/
│   │   ├── work_activities/
│   │   ├── mcp_profile/
│   │   └── trends/
│   └── field_benchmarks/        — Active question bucket
│       ├── README.md
│       ├── field_benchmarks_report.md
│       ├── automation_share/
│       ├── wage_impact/
│       ├── utah_benchmarks/
│       ├── theoretical_vs_confirmed/
│       ├── sector_breakdown/
│       ├── work_activity_comparison/
│       └── platform_landscape/
│   ├── state_clusters/          — Active question bucket
│   │   ├── README.md
│   │   ├── state_clusters_report.md
│   │   ├── risk_profile/        — Cluster by employment-weighted risk tier distribution
│   │   ├── activity_signature/  — Cluster by GWA share of AI-exposed employment
│   │   ├── agentic_profile/     — Cluster by agentic intensity (agentic/confirmed) per sector
│   │   ├── adoption_gap/        — Cluster by ceiling-confirmed gap ratio per sector
│   │   └── cluster_convergence/ — ARI matrix + state stability across all 5 schemes
│   └── time_trends/             — Active question bucket
│       ├── README.md
│       ├── time_trends_report.md
│       ├── trajectory_shapes/   — Classify occupations by growth pattern (6 types)
│       ├── tier_churn/          — Exposure tier transitions and sector stability
│       ├── confirmed_ceiling_convergence/ — Confirmed/ceiling ratio trend nationally + by sector
│       ├── wa_tipping_points/   — IWA threshold crossings (10%, 33%, 66%) and approaching IWAs
│       └── occs_timeline/       — Full time-series for the 29 named occupations of interest
├── question_findings/           — Flat copies of question .md reports
└── report/
    └── report.md                — Rolling aggregate report
```

---

## Compute Access

```python
# Shared config helpers
from analysis.config import (
    ANALYSIS_CONFIGS,         # dict[key → dataset_name] — five canonical configs
    ANALYSIS_CONFIG_LABELS,   # dict[key → display label]
    ANALYSIS_CONFIG_SERIES,   # dict[key → list[dataset_name]] — time series per config
    OCCS_OF_INTEREST,         # list[str] — 29 named occupations
    get_pct_tasks_affected,   # (dataset_name, method, use_auto_aug) → pd.Series
    make_config, run_occ_query, ensure_results_dir,
)

# SKA computation (real-time, not cached)
from analysis.data.compute_ska import load_ska_data, compute_ska
# SKAResult fields: .ai_capability, .eco_baseline, .eco_baseline_p95, .occ_gaps, .occ_element_scores

# Backend compute (same engine as the dashboard)
from backend.compute import get_group_data, get_explorer_occupations, load_eco_raw

# Chart styling
from analysis.utils import style_figure, save_figure, save_csv, COLORS, FONT_FAMILY
```

### get_pct_tasks_affected()

```python
pct = get_pct_tasks_affected("All 2026-02-18")   # → pd.Series keyed by title_current
# Equivalent to: make_config + get_group_data at agg_level="occupation", top_n=9999
```

### get_wa_data() pattern (work activity analysis)

```python
from backend.compute import compute_work_activities

def get_wa_data(dataset_name: str, level: str = "iwa") -> pd.DataFrame:
    """Get work activity exposure for one pre-combined dataset at a given level."""
    settings = {
        "selected_datasets": [dataset_name],
        "combine_method": "Average",
        "method": "freq",
        "use_auto_aug": True,
        "physical_mode": "all",
        "geo": "nat",
        "sort_by": "workers_affected",
        "top_n": 9999,
    }
    result = compute_work_activities(settings)
    # Most ANALYSIS_CONFIGS are is_aei=False → results come back as "mcp_group"
    # Exception: agentic_confirmed uses AEI API 2026-02-12 (is_aei=True) → comes back as "aei_group"
    # (uses eco_2025 O*NET baseline; consistent across all five configs)
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])  # level: "gwa", "iwa", or "dwa"
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# Each row: {"category": str, "pct_tasks_affected": float,
#             "workers_affected": float, "wages_affected": float}

# Note: raw AEI datasets (is_aei=True, e.g. "AEI Both 2026-02-12") use eco_2015
# baseline and come back as "aei_group". Do NOT mix aei_group and mcp_group results.
# Four of five ANALYSIS_CONFIGS are is_aei=False (eco_2025 baseline for WA).
# agentic_confirmed (AEI API 2026-02-12) is is_aei=True → eco_2015 baseline for WA, aei_group path.
```

### compute_ska() pattern

```python
ska_data = load_ska_data()   # load once per script

for config_key, dataset_name in ANALYSIS_CONFIGS.items():
    pct = get_pct_tasks_affected(dataset_name)
    result = compute_ska(pct, ska_data)
    # result.occ_gaps: title_current, skills_gap, abilities_gap, knowledge_gap, overall_gap
    # result.occ_element_scores["skills"]: title_current, element_name, occ_score, ai_score, gap
```

---

## SKA Formula (locked-in spec)

**Input:** `pct_tasks_affected` Series (title_current → 0-100)

**Per (occ, element) row where `importance ≥ 3`:**
- `occ_score = importance × level`
- `ai_product = (pct_tasks_affected / 100) × importance × level`

**Per element (across all matched occupations):**
- `ai_capability = 95th percentile of ai_product`
- `eco_baseline = mean of occ_score` (no pct weighting — reference only)

**Per (occ, element):**
- `gap = ai_capability − occ_score`
  - `gap > 0` → AI exceeds this occupation's need (leverage AI here)
  - `gap < 0` → Human advantage (focus training here)

**Per (occ, element) — percentage framing:**
- `ai_pct_occ = ai_score / occ_score × 100`

**Per occupation:**
- `skills_gap = mean(gap) across all skills elements`
- `abilities_gap = mean(gap) across all abilities elements`
- `knowledge_gap = mean(gap) across all knowledge elements`
- `overall_gap = mean(skills_gap, abilities_gap, knowledge_gap)`
- `overall_pct = sum(ai_score) / sum(occ_score) × 100` (ratio-of-sums across all elements)
- `skills_pct, abilities_pct, knowledge_pct` — same ratio-of-sums pattern per element type

**Worker resilience ranking:** sort by `gap` ascending (most negative = biggest human advantage = where to invest).

**SKA trend:** recompute at first and last date of `ANALYSIS_CONFIG_SERIES[config_key]` only; compute `delta_gap = last_overall_gap − first_overall_gap`.

**Note:** The 95th percentile threshold for `ai_capability` is defended in the notebook `analysis/data/ai_capability_method_comparison.ipynb`.

---

## Risk Scoring Flags

Computed per occupation, based on the primary config (`all_confirmed`) unless otherwise noted.

**Weighted scoring:** Flags 1–2 (strongest exposure signals) get weight 2. Flags 3–8 (supporting signals) get weight 1. Maximum possible score = 10.

| Flag | Weight | Condition |
|------|--------|-----------|
| 1 | 2 | `pct_tasks_affected > 50%` (absolute threshold) |
| 2 | 2 | `overall_pct > median` (SKA percentage) |
| 3 | 1 | `pct_delta > 0 AND > median(pct_delta)` |
| 4 | 1 | `ska_delta > 0 AND > median(ska_delta)` |
| 5 | 1 | `job_zone ∈ {1, 2, 3}` |
| 6 | 1 | `outlook ∈ {2, 3}` |
| 7 | 1 | `n_software > median` |
| 8 | 1 | `auto_avg_with_vals > median` |

**Exposure gate:** If `pct_tasks_affected < 33%`, the occupation cannot be classified as high risk regardless of weighted score — downgrades to Mod-High.

**Tiers:** 8–10 = High, 5–7 = Mod-High, 3–4 = Mod-Low, 0–2 = Low.

---

## Output Standards

### Figures
- Use `style_figure()` and `save_figure()` from `analysis.utils`. Never hardcode colors.
- Save to `results/figures/` (all figures) and `figures/` (committed key figures).
- Run `run.py` copies key figures from results to the committed `figures/` dir.

### CSVs
- Always include headers and descriptive column names.
- Round floats to 2–4 decimal places as appropriate.

### Reports

**Sub-question reports** (`<sub-folder>/<name>_report.md`):
- Full narrative with inline figures (referenced from the sub-folder's committed `figures/` dir).
- Ends with a Config section (dataset, method, settings used) and a Files table.
- `run.py` calls `generate_pdf(md_path, pdf_path)` at the end.

**Aggregate reports** (`<bucket>/<bucket>_report.md`):
- One per top-level question bucket. See `job_exposure/job_exposure_report.md` as the canonical example.
- Structure: config header line → opening summary paragraph → numbered sections (one per sub-question, each opening with `*Full detail: [...](...)*` link) → Cross-Cutting Findings → Key Takeaways → Sub-Report Index table → Config Reference table.
- Each section must embed at least one figure from the relevant sub-folder's committed `figures/` dir using relative paths (e.g., `sector_footprint/figures/aggregate_totals.png`).
- Written in the conversational-analytical voice from `writing_style_reference.md` — reasoning through findings, not summarizing bullet points.

---

## Common Pitfalls

- **SKA title matching**: O*NET v30.1 `Title` matches `title_current` in eco_2025. If <90% match, investigate before proceeding.
- **SKA importance filter is per-row**: importance ≥ 3 is applied per (occ, element). A skill can be important in one occupation and not another.
- **pct is already 0-100**: `get_pct_tasks_affected()` returns values in 0-100 range. Do not divide by 100 before passing to compute_ska — it handles the division internally.
- **Trend flags need at least 2 dates**: configs with only one date (e.g., Microsoft) cannot produce trend flags.
- **Pivot distance**: use `min(10, n)` if a job zone has fewer than 10 high-risk or low-risk occupations.
- **n_software from tech_skills_simple.csv**: joined by `title` not `soc_code`, since title_current is what we have at the occ level.
- **Outlook is a non-linear 0-5 scale**: ECO 2025 DWS star rating is NOT ordered severity. 5=strongest outlook+high wages, 4=good outlook+high wages, 3=moderate outlook+low-mod wages, 2=high wages+limited outlook, 1=low wages+strong outlook, 0=limited outlook+low wages. Ratings 1 and 2 represent different tradeoffs, not ordered severity. Based on Utah projected openings (90%), growth rate (10%), and median wages.
- **MCP standalone for bias testing**: `"MCP Cumul. v4"` can be used to test zone/sector exposure patterns without user self-selection bias (it's tool specs, not usage data). Note that MCP has its own bias: tools are built for higher-zone workflows.
