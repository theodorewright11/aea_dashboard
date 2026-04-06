# ANALYSIS_ARCHITECTURE.md — Analysis System Architecture

Technical reference for the `analysis/` folder. Does not repeat information in the main `ARCHITECTURE.md`.

---

## Folder Structure

```
analysis/
├── ANALYSIS_CLAUDE.md       — Agent rules for analysis work
├── ANALYSIS_PRD.md          — Question catalog, audiences, five configs
├── ANALYSIS_ARCHITECTURE.md — This file
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
│   └── job_exposure/            — Active question bucket
│       ├── README.md
│       ├── job_exposure_report.md
│       ├── exposure_state/
│       ├── job_risk_scoring/
│       ├── worker_resilience/
│       ├── pivot_distance/
│       ├── audience_framing/
│       └── occs_of_interest/
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
# SKAResult fields: .ai_capability, .eco_baseline, .occ_gaps, .occ_element_scores

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

**Per occupation:**
- `skills_gap = mean(gap) across all skills elements`
- `abilities_gap = mean(gap) across all abilities elements`
- `knowledge_gap = mean(gap) across all knowledge elements`
- `overall_gap = mean(skills_gap, abilities_gap, knowledge_gap)`

**Worker resilience ranking:** sort by `gap` ascending (most negative = biggest human advantage = where to invest).

**SKA trend:** recompute at first and last date of `ANALYSIS_CONFIG_SERIES[config_key]` only; compute `delta_gap = last_overall_gap − first_overall_gap`.

---

## Risk Scoring Flags

Computed per occupation, based on the primary config (`all_confirmed`) unless otherwise noted.

**Weighted scoring:** Flags 1–4 (direct exposure signal) get weight 2. Flags 5–7 (structural vulnerability) get weight 1. Maximum possible score = 11.

| Flag | Weight | Condition | Notes |
|------|--------|-----------|-------|
| 1 | 2 | `pct_tasks_affected > median(all occs)` | Varies by config |
| 2 | 2 | `overall_gap > median(all occs)` | SKA gap; varies by config |
| 3 | 2 | `pct_delta > 0 AND pct_delta > median(pct_delta)` | pct trend; median is of ALL growth (incl. negative) |
| 4 | 2 | `ska_delta > 0 AND ska_delta > median(ska_delta)` | SKA gap trend |
| 5 | 1 | `job_zone ∈ {1, 2, 3}` | From eco_2025 |
| 6 | 1 | `outlook ∈ {2, 3}` | DWS star rating; 1 = good outlook/low wages |
| 7 | 1 | `n_software > median(all occs)` | From tech_skills_simple.csv |

**Exposure gate:** If `pct_tasks_affected < 33%`, the occupation cannot be classified as high risk regardless of weighted score.

**Tiers:** 8–11 = high risk, 4–7 = moderate, 0–3 = low.

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
- Each sub-question has a `<name>_report.md` with full narrative, inline figures, and a Config section.
- `run.py` calls `generate_pdf(md_path, pdf_path)` at the end.

---

## Common Pitfalls

- **SKA title matching**: O*NET v30.1 `Title` matches `title_current` in eco_2025. If <90% match, investigate before proceeding.
- **SKA importance filter is per-row**: importance ≥ 3 is applied per (occ, element). A skill can be important in one occupation and not another.
- **pct is already 0-100**: `get_pct_tasks_affected()` returns values in 0-100 range. Do not divide by 100 before passing to compute_ska — it handles the division internally.
- **Trend flags need at least 2 dates**: configs with only one date (e.g., Microsoft) cannot produce trend flags.
- **Pivot distance**: use `min(10, n)` if a job zone has fewer than 10 high-risk or low-risk occupations.
- **n_software from tech_skills_simple.csv**: joined by `title` not `soc_code`, since title_current is what we have at the occ level.
- **Outlook 1 = good outcome**: BLS DWS rating 1 means "bright outlook, high wages" — it is NOT the worst category. Flag only outlook 2 and 3 as at-risk.
