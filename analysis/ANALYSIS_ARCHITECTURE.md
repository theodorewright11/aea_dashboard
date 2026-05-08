# ANALYSIS_ARCHITECTURE.md — Analysis System Architecture

Technical reference for the `analysis/` folder: folder map, compute access, locked-in formulas, output standards, and cross-references between live components.

For *what* the analysis system is for, see `ANALYSIS_PRD.md`. For *how to work in it*, see `ANALYSIS_CLAUDE.md`.

---

## Folder Structure

```
analysis/
├── ANALYSIS_PRD.md          — What the analysis system is for
├── ANALYSIS_CLAUDE.md       — Agent rules for analysis work
├── ANALYSIS_ARCHITECTURE.md — This file
├── config.py                — Shared paths, ANALYSIS_CONFIGS, ANALYSIS_CONFIG_SERIES,
│                              OCCS_OF_INTEREST, get_pct_tasks_affected(), helpers
├── utils.py                 — Chart styling (style_figure, save_figure), PDF generation,
│                              COLORS, FONT_FAMILY, CATEGORY_PALETTE
├── writing_style_reference.md — Style guide for question-style narrative reports
│                                (gitignored; lifted out of archived questions/)
├── data/
│   ├── skills_v30.1.csv         — O*NET v30.1 skills (base file)
│   ├── abilities_v30.1.csv      — O*NET v30.1 abilities (base file)
│   ├── knowledge_v30.1.csv      — O*NET v30.1 knowledge (base file)
│   ├── technology_skills_v30.1.csv — O*NET v30.1 tech skills (base file)
│   ├── tech_skills_simple.csv   — Static: soc_code, title, n_software (generated)
│   ├── compute_ska.py           — Real-time SKA gap computation module
│   ├── compute_tech_skills.py   — Generates tech_skills_simple.csv
│   └── ai_capability_method_comparison.ipynb — Defends 95th-percentile threshold
├── paper/                   — Research paper infrastructure
│   ├── paper_config.py          — PAPER_PALETTE, chart constants, style_paper_figure()
│   ├── writing_style_source.md  — ~30 pages of source writing for style calibration
│   ├── paper_writing_style.md   — Condensed dos/don'ts for paper writing
│   ├── working_paper_outline.md — Draft structure reference (not final)
│   └── results/                 — Results section (NOT gitignored — section content)
│       ├── results.md           — Assembled Results section (Parts 1–3)
│       ├── part_1/              — Scale, Convergence, Growth — first draft complete
│       ├── part_2/              — Characterization: Where AI Exposure Falls
│       └── part_3/              — Action: What To Do About It
│           Each part has: run.py, README.md, part_N.md, results/ (gitignored),
│           figures/ (committed). See each part's README for chart-by-chart detail.
│
├── exploratory/             — Live exploratory analysis. Folder is gitignored
│   │                          except for two carved-out paperinfra folders
│   │                          (see "Gitignore exceptions" below). Each sub-folder
│   │                          has run.py, README.md, <name>_report.md, results/.
│   │                          Naming convention: <bucket>_<topic> for
│   │                          discoverability via `ls`.
│   │
│   │   ── paperinfra_*  — Mirrors / variants of paper figures (committed)
│   ├── paperinfra_all_charts/   — Mirror of every committed paper figure
│   │                              (part_1/2/3) regenerated via sync script,
│   │                              with all_paper_charts.md listing each one.
│   │                              Has gitignored offshoots/ sandbox for variants
│   │                              (e.g. simple_mean_convergence,
│   │                              major_top10_trends_*, weighting_config_test)
│   ├── paperinfra_aei_only/     — Same mirror with all_confirmed swapped to
│   │                              AEI-only (no Microsoft). Gitignored.
│   ├── paperinfra_appendix/     — Auxiliary paper figures (phys_zone_faceted,
│   │                              ska_full). Committed.
│   │
│   │   ── extcompare_*  — Comparisons against external indices (gitignored)
│   ├── extcompare_schaal/       — Replicates Part 1+2 chart types using
│   │                              Schaal 2025 per-task scores in place of our
│   │                              auto-aug. 5 score variants × 11 PNGs.
│   ├── extcompare_indices/      — SOC convergence heatmap of our 9
│   │                              sources/configs vs. all 16 external indices
│   │                              (Schaal, Eloundou, Webb, SML, AIOE,
│   │                              Frey-Osborne, Autor). Plus Schaal task-level
│   │                              scatter and group-level heatmaps.
│   ├── extcompare_mertens/      — Mertens 2026 "tide vs wave" replication;
│   │                              uses paper βs to flag forward-risk occs.
│   ├── extcompare_eloundou/     — T0–T4 label count matrices and auto-aug
│   │                              distributions joined onto our datasets via
│   │                              Eloundou's labeling TSV.
│   │
│   │   ── audit_*  — Methodology audits / robustness (gitignored)
│   ├── audit_task_properties/   — 12 LLM-rated task properties (m/d/s/...) vs.
│   │                              our pct; how far you can get with no usage data.
│   ├── audit_risk_score/        — Audits the 8-flag job-risk composite;
│   │                              produces the 56-occ "focused set" used by
│   │                              paper part_3's risk_score_5f figure.
│   │                              IMPORTED BY paper/results/part_3/run.py.
│   ├── audit_physical_delim/    — How much of paper convergence is just the
│   │                              physical/non-physical cut.
│   ├── audit_microsoft_iwa/     — Microsoft's marginal contribution beyond AEI;
│   │                              IWA-level extras audit. Closes loop with the
│   │                              AI-share filter solution.
│   ├── audit_pct_norm_eco/      — AI usage Σpct vs. economic baseline;
│   │                              intensity-anchor lift charts. Source of
│   │                              paper part_3's intensity_anchor_fulleco
│   │                              (chart 15). IMPORTED BY paper/results/part_3/run.py
│   │                              (function-level, skips gracefully if absent).
│   │
│   │   ── deepdive_*  — Per-element / structural deep dives (gitignored)
│   ├── deepdive_ska_categories/ — Part 2 SKA chart rolled up to O*NET native
│   │                              category groupings.
│   ├── deepdive_onet_economy/   — 62-chart structural panorama of the U.S.
│   │                              occupational economy (no AI data).
│   │
│   └── claude_lab/              — Claude's autonomous research workspace.
│                                  Has its own CLAUDE.md, research_log.md,
│                                  INVENTORY.md. Each thread is a sub-folder
│                                  with run.py + results/ + notes.md.
│
└── _archive/                — Frozen historical work (do not edit)
    ├── questions/               — Question-bucket analysis system (8 active
    │                              buckets when frozen). Each bucket has
    │                              run.py + bucket_report.md + sub-folders.
    │                              Patterns referenced from this code (SKA
    │                              formula, risk scoring) remain live.
    ├── question_findings/       — Flat copies of bucket reports for browsing
    ├── report/                  — Rolling aggregate reports (report.md +
    │                              report_brief.md). Image paths use
    │                              ../questions/... which still resolves
    │                              after the move.
    └── exploratory_old/         — Stale exploratory analyses superseded by
                                   paper sections, question buckets, or other
                                   exploratory folders. Includes job_breakdown,
                                   ska_levels, zone_pivot_anatomy,
                                   physical_informational_divide,
                                   method_weighting_sensitivity,
                                   gpts_are_gpts_comparison, aioe_comparison.
```

### Gitignore exceptions

The exploratory folder is gitignored (`analysis/exploratory/*`) with two carved-out commits:

```
!analysis/exploratory/paperinfra_all_charts/
!analysis/exploratory/paperinfra_all_charts/**
!analysis/exploratory/paperinfra_appendix/
!analysis/exploratory/paperinfra_appendix/**
analysis/exploratory/paperinfra_appendix/results/         (re-excluded — regenerable)
analysis/exploratory/paperinfra_all_charts/offshoots/     (re-excluded — sandbox)
```

Outside these exceptions, do not use `git add -f`.

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
# SKAResult fields: .ai_capability, .eco_baseline, .eco_baseline_p95,
#                   .occ_gaps, .occ_element_scores

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
    # Exception: agentic_confirmed uses AEI API (is_aei=True) → "aei_group"
    group = result.get("mcp_group") or result.get("aei_group")
    if group is None:
        return pd.DataFrame()
    rows = group.get(level, [])  # level: "gwa", "iwa", or "dwa"
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# Each row: {"category": str, "pct_tasks_affected": float,
#             "workers_affected": float, "wages_affected": float}
#
# Note: raw AEI datasets (is_aei=True, e.g. "AEI Both 2026-02-12") use eco_2015
# baseline → "aei_group". Do NOT mix aei_group and mcp_group results.
# Four of five ANALYSIS_CONFIGS are is_aei=False (eco_2025 baseline for WA).
# agentic_confirmed (AEI API 2026-02-12) is is_aei=True → eco_2015 baseline.
```

### compute_ska() pattern

```python
ska_data = load_ska_data()   # load once per script

for config_key, dataset_name in ANALYSIS_CONFIGS.items():
    pct = get_pct_tasks_affected(dataset_name)
    result = compute_ska(pct, ska_data)
    # result.occ_gaps: title_current, skills_gap, abilities_gap,
    #                  knowledge_gap, overall_gap
    # result.occ_element_scores["skills"]: title_current, element_name,
    #                                       occ_score, ai_score, gap
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

**Note:** The 95th percentile threshold for `ai_capability` is defended in `analysis/data/ai_capability_method_comparison.ipynb`.


---

## Cross-References (live ↔ live)

The paper imports from two exploratory folders (function-level, with try/except so the paper still runs if exploratory is absent):

- `paper/results/part_3/run.py` → `analysis.exploratory.audit_pct_norm_eco.run` and `.run_v3` (chart 15: `intensity_anchor_fulleco`)
- `paper/results/part_3/run.py` → `analysis.exploratory.audit_risk_score.run` (5f flags + focused-set helpers for `risk_score_5f`)

If you rename or move either exploratory folder, update both imports in `paper/results/part_3/run.py` and the corresponding lines in `paper/results/part_3/README.md`.

The paper also reuses the tech_skills pipeline conceptually from the archived `_archive/questions/economic_footprint/skills_landscape/` (reimplemented in paper styling), but no Python import dependency.

---

## Output Standards

### Figures
- Use `style_figure()` and `save_figure()` from `analysis.utils`. Never hardcode colors — use `COLORS`, `CATEGORY_PALETTE`, `FONT_FAMILY`.
- Save to `results/figures/` (all figures); copy key figures to `figures/` (committed) at the end of `run.py`.
- Paper figures additionally use `style_paper_figure()` and `PAPER_PALETTE` from `paper/paper_config.py`.

### CSVs
- Always include headers and descriptive column names.
- Round floats to 2–4 decimal places as appropriate.

### Reports
- Each exploratory sub-folder has a `<name>_report.md` with full narrative and inline figures referencing `results/figures/` paths (which work locally after running the script).
- For paper-style writing, see `paper/paper_writing_style.md` and `paper/writing_style_source.md`.
- For question-style narrative writing (now archived), see `writing_style_reference.md`.

### Chart formatting
- Horizontal bar charts using `make_horizontal_bar` must pass the DataFrame sorted `ascending=False` (largest first). `make_horizontal_bar` uses `autorange="reversed"` on the y-axis — passing ascending=True will render smallest at top.
- For raw `go.Figure` horizontal bars (without `make_horizontal_bar`), sort `ascending=True` (smallest first) so the largest value renders at the top.
- State/geo labels should be uppercase in all bar charts.
- Reports use opening paragraphs (no `## TLDR` heading and no `**TLDR:**` prefix).

---

## Common Pitfalls

- **SKA title matching**: O*NET v30.1 `Title` matches `title_current` in eco_2025. If <90% match, investigate before proceeding.
- **SKA importance filter is per-row**: importance ≥ 3 is applied per (occ, element). A skill can be important in one occupation and not another.
- **pct is already 0-100**: `get_pct_tasks_affected()` returns values in 0-100 range. Do not divide by 100 before passing to compute_ska — it handles the division internally.
- **Trend flags need at least 2 dates**: configs with only one date (e.g., Microsoft) cannot produce trend flags.
- **Pivot distance**: use `min(10, n)` if a job zone has fewer than 10 high-risk or low-risk occupations.
- **n_software from tech_skills_simple.csv**: joined by `title` not `soc_code`, since title_current is what we have at the occ level.
- **Outlook is non-linear, not ordered severity**: ECO 2025 DWS star rating represents tradeoffs, not severity. 5=strong outlook+high wages, 4=good outlook+high wages, 3=moderate, 2=high wages+limited outlook, 1=low wages+strong outlook, 0=limited+low wages. Based on Utah projected openings (90%), growth rate (10%), median wages.
- **MCP standalone for bias testing**: `"MCP Cumul. v4"` can test zone/sector exposure patterns without user self-selection bias (it's tool specs, not usage data). Note MCP has its own bias: tools built for higher-zone workflows.
- **SKA category analysis uses ai_pct_occ (not ai_pct_eco_mean)**: When computing SKA averages by occupation category, use `ai_pct_occ` (per-occ: ai_score / occ_score × 100) averaged across occupations. `ai_pct_eco_mean` divides by the mean occ_score across all occupations, which is different.
- **`pct_tasks_affected` is already a ratio-of-totals (0-100)**: never average it across occupations to get a group pct — re-derive from task_comps.
- **all_confirmed series starts at March 2025**: the 2024-09-30 and 2024-12-23 dates have been removed from all trend series. Sep 2024 was anchored by Microsoft Copilot only (AEI starts Dec 2024); Dec 2024 is similarly excluded. Do not re-add either 2024 date.
- **Part 1 temporal_tables historical rows**: the two cream rows above the line-chart series (Sep 2024, Dec 2024) pull task counts from the SAME combined dataset family the line chart uses — `AEI Both + Micro 2024-09-30/2024-12-23` for All Confirmed; `All 2024-09-30/2024-12-23` for Ceiling. Do NOT revert to `Microsoft` and `AEI Conv 2024-12-23` alone — that under-counts the Dec 2024 row.
- **Part 3 intensity_anchor_fulleco colorbar (% Tasks Exposed)**: Pull colorbar values via `_run_config(PRIMARY_DATASET, "major")` (the dashboard pipeline that drives Part 2 `major_categories`). Do NOT use `compute_major_pct_tasks_affected` from `audit_pct_norm_eco/run_v3.py` — that function restricts to rated task-occ pairs only and produces 53–76% values that don't match the rest of the paper.
