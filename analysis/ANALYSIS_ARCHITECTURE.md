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
│   │   ├── worker_resilience/          — SKA gap analysis; tips for 3 occupations
│   │   │   └── ska_deep_dive/          — Element trends, cross-config, category breakdown, most-subsumed occs
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
│   ├── time_trends/             — Active question bucket
│   │   ├── README.md
│   │   ├── time_trends_report.md
│   │   ├── trajectory_shapes/   — Classify occupations by growth pattern (6 types)
│   │   ├── tier_churn/          — Exposure tier transitions and sector stability
│   │   ├── confirmed_ceiling_convergence/ — Confirmed/ceiling ratio trend nationally + by sector
│   │   ├── wa_tipping_points/   — IWA threshold crossings (10%, 33%, 66%) and approaching IWAs
│   │   └── occs_timeline/       — Full time-series for the 29 named occupations of interest
│   ├── workforce_meeting/       — Active question bucket (presentation deliverable)
│   │   ├── README.md
│   │   ├── workforce_meeting_report.md
│   │   ├── run.py
│   │   └── figures/             — 14 committed chart PNGs
│   └── workforce_meeting_v2/    — V2: charts only, larger fonts, non-technical framing
│       ├── README.md
│       ├── workforce_meeting_v2_report.md
│       ├── run.py
│       └── figures/             — 11 committed chart PNGs
├── question_findings/           — Flat copies of question .md reports
├── report/
│   └── report.md                — Rolling aggregate report
├── paper/                       — Research paper infrastructure
│   ├── paper_config.py          — PAPER_PALETTE, chart constants, style_paper_figure()
│   ├── writing_style_source.md  — ~30 pages of source writing for style calibration
│   ├── paper_writing_style.md   — Condensed dos/don'ts for paper writing
│   ├── working_paper_outline.md — Draft structure reference only (not final, may be outdated)
│   └── results/                 — Results section (NOT gitignored — section name)
│       ├── results.md           — Assembled Results section (Parts 1–3; update as parts complete)
│       ├── part_1/              — Scale, Convergence, Growth — FIRST DRAFT COMPLETE
│       │   ├── run.py, README.md, part_1.md, results/ (gitignored), figures/ (committed)
│       ├── part_2/              — Characterization: Where AI Exposure Falls — FIRST DRAFT COMPLETE
│       │   ├── run.py, README.md, part_2.md, results/ (gitignored), figures/ (committed)
│       └── part_3/              — Action: What To Do About It — FIGURES + SCAFFOLDING (no prose yet)
│           ├── run.py, README.md, part_3.md, results/ (gitignored), figures/ (committed)
│           ├── Figures: property_biplot, tech_commodities, conv_vs_agentic, gap_to_ceiling,
│           │            risk_x_ska, pct_x_nt_de, phys_info_frictions, tacit_duration_safe
│           └── Cross-references: job_exposure/job_risk_scoring (risk_scores_primary.csv),
│                                 job_exposure/worker_resilience (occ_gaps_summary.csv),
│                                 economic_footprint/skills_landscape (tech_skills pipeline,
│                                 reimplemented in paper styling),
│                                 data/final_eco_2025_with_task_properties.csv (12 props)
└── exploratory/                 — Gitignored entirely. Nothing in this folder is ever
    │                              committed — do not use git add -f. One-off charts only;
    │                              no reports fed into question_findings/ or report/.
    │                              Each sub-folder has: run.py, README.md, <name>_report.md
    │                              (findings writeup with inline figures referencing
    │                              results/figures/ paths), and results/ (auto-created).
    ├── job_breakdown/           — Per-occupation SKA + task breakdown for 3 EOR-adjacent
    │                              occupations (HR Specialists, Compensation Specialists,
    │                              Customer Service Reps); replicates worker_resilience pattern
    ├── ska_levels/              — AI imp×lv vs. workforce benchmarks for every SKA element
    ├── zone_pivot_anatomy/      — Why zone 3 peaks on pivot cost; overlap structure and
    │                              sector composition of at-risk occupations by zone
    ├── physical_informational_divide/ — Physical vs. informational occupation split;
    │                              structural task distributions (GWA/IWA/DWA 3×2 panels);
    │                              AI exposure analysis: pct distribution, IWA workers
    │                              concentration, auto-aug breakdown (task type × coverage ×
    │                              dataset), GWA concentration curve, auto-aug vs pct scatter
    ├── aioe_comparison/         — Felten/Raj/Seamans AIOE 52×10 matrix vs. our
    │                              pct_tasks_affected. Per-occ AIOE score = ratio-of-sums
    │                              of imp×lv×ability_cap over imp≥3 ability rows. Three
    │                              variants: row-mean across 10 apps, Language Modeling
    │                              column only, Reading Comprehension column only. 18 charts
    │                              spanning occ-level scatter, SOC-level convergence (focused
    │                              + all-sources), 4-aggregate-panel ability ranking (sorted
    │                              by mean/RC/LM), per-ability SKA-aggregate vs AIOE
    │                              comparisons, per-AI-app ρ breakdown at 3 SKA aggregates,
    │                              occ-level full heatmap.
    ├── claude_lab/              — Claude's autonomous research workspace on the AEA
    │                              data. Operates as an independent researcher, not a
    │                              directed analyst. Has its own CLAUDE.md (agent spec
    │                              with autonomous-researcher framing), research_log.md
    │                              (single rolling synthesis updated every session),
    │                              INVENTORY.md (meta log of sub-folders, open threads,
    │                              accreted conventions, paper-flag candidates),
    │                              README.md, and lib/ for shared helpers. Each thread
    │                              is a named sub-folder with run.py + results/ +
    │                              notes.md (and optionally <topic>_report.md).
    │                              Synthesis reports may live at the workspace root.
    │                              Folder is gitignored entirely. Folder used to be
    │                              called action_levers/; the seed sub-folder
    │                              initial_action_charts/ retains that historical name
    │                              and produces six charts on what to do about
    │                              widespread exposure (complementarity quadrant,
    │                              sectoral velocity, wage resilience matrix, resilience
    │                              differential, trade-up corridors, bottleneck
    │                              activity atlas) — all under all_confirmed. Future
    │                              sub-folders pursue whatever Claude finds worth
    │                              investigating. Promotion to paper/ is gated by the
    │                              user.
    ├── schaal_substitution/     — Replicates the chart types from
    │                              `paper/results/part_1` + `part_2` (minus
    │                              correlations and temporal) using Schaal 2025's
    │                              per-task scores from merged_tasks_full.csv
    │                              in place of our pipeline's auto_aug_mean.
    │                              Schaal score normalized as score / 2 to
    │                              match the original auto_aug_mean / 5 0-1
    │                              multiplier mechanic. Two versions per chart:
    │                              "economy" (Schaal applied to every eco_2025
    │                              task with a score) and "confirmed" (Schaal
    │                              applied only to task-occ pairs that ALSO
    │                              appear in all_confirmed). Five score
    │                              variants run through the full pipeline:
    │                              auto_avg (Schaal Overall, eq. 1), pv_avg
    │                              (Performance Variance / Moravec proxy),
    │                              da_avg (Data Abundance), tk_avg (Tacit
    │                              Knowledge — high = MINIMAL TK required =
    │                              MORE automatable, system-prompt convention),
    │                              ag_avg (Algorithmic Efficiency Gap). Six
    │                              chart types per variant (overview, phys/info,
    │                              job zone, GWA, major categories, SKA via
    │                              compute_ska piped with Schaal-derived pct)
    │                              x 11 PNGs each + 1 cross-variant comparison
    │                              chart = 56 PNGs total in
    │                              results/figures/{auto,pv,da,tk,ag,_comparison}/.
    │                              Per-variant findings: DA closest to
    │                              observed-usage (Office/Admin + Computer/Math
    │                              top); TK is the cleanest Moravec test
    │                              (high-skill expert work consistently bottom
    │                              — supports seniority-biased technological
    │                              change); PV inverts intuitions
    │                              (Arts/Education on top via high human
    │                              performance variance); AG essentially a
    │                              phys/info cut. No single subhypothesis
    │                              reproduces Schaal Overall — the four-factor
    │                              average is doing real work.
    ├── external_indices_correlation/ — Three analyses against Schaal 2025
    │                              (Cambridge ERA AI Governance Research Fellowship,
    │                              "A theory-based AI automation exposure index:
    │                              Applying Moravec's Paradox to the US labor
    │                              market") replication data.
    │                              (1) SOC convergence heatmap: Spearman ρ of
    │                              our 4 internal sources + 5 ANALYSIS_CONFIGS
    │                              (9 rows) against all 16 external AI/automation
    │                              exposure indices in `Comparison of Indices.csv`
    │                              — Schaal's own Moravec index (overall auto_w
    │                              + 4 subhypotheses PV/DA/TK/AG; tk_w is
    │                              inverted-coded, high = MORE tacit knowledge
    │                              required = LESS automatable), Eloundou α/β/γ,
    │                              Webb software/robot/ai, SML, AIOE base felten,
    │                              Frey-Osborne, Autor routine cog/manual. Four
    │                              SOC levels stacked vertically, pairwise dropna
    │                              per cell, diverging color scale, significance
    │                              asterisks. Negative ρ against pre-LLM indices
    │                              reproduces Schaal's Figure 4 paradigm-shift
    │                              finding from a third independent methodology.
    │                              (2) Task-level scatter: Schaal's per-task
    │                              auto_avg from `merged_tasks_full.csv` vs our
    │                              auto_aug_mean per (task_normalized,
    │                              soc_code_2019_full). 5-panel one-per-config
    │                              + 4-panel subhypothesis breakdown. Joins on
    │                              normalized task text + 2019 SOC; AEI-only
    │                              datasets (only soc_code_2010 in file) bridged
    │                              to 2019 via the AEI Both + Micro crosswalk;
    │                              GWA/IWA/DWA expansion deduped via
    │                              groupby([task_norm, soc]).first(). Task-level
    │                              ρ (0.07–0.30) is much weaker than occ-level
    │                              ρ (0.5–0.6) — agreement is between-occupation,
    │                              not within. (3) Group-level auto_aug vs
    │                              Schaal heatmap (group_auto_aug_vs_schaal.png):
    │                              two stacked 4×5 heatmaps, rows = SOC levels,
    │                              cols = Schaal's 5 score columns from
    │                              merged_tasks_full.csv. Cells = Spearman ρ
    │                              between group-level avg auto_aug_mean (from
    │                              all_confirmed) and group-level avg Schaal
    │                              score. Two methods applied symmetrically:
    │                              Method A zero-fill (avg over ALL eco
    │                              task-occ pairs in group, missing = 0) and
    │                              Method B rated-only (only pairs with both
    │                              ratings). Schaal DA strongest predictor
    │                              (ρ ≈ 0.83 at major under Method A); Schaal
    │                              TK negative (observed Claude usage
    │                              concentrates in high-tacit-knowledge fields).
    │                              Four PNGs + 5 CSVs total.
    ├── task_properties_correlation/ — Correlates 12 LLM-rated task
    │                              properties (m, d, s, r, h, e, t, tf, df,
    │                              de, nt, ac) from
    │                              `data/final_eco_2025_with_task_properties.csv`
    │                              against 4 internal sources + 6 configs
    │                              (5 ANALYSIS_CONFIGS + new
    │                              `all_confirmed_conservative` from
    │                              `final_all_confirmed_usage_ms_nonphysical_2026-02-12.csv`,
    │                              registered in backend/config.py as
    │                              "AEI Both + Micro Conservative 2026-02-12")
    │                              at major/minor/broad/occupation. Two
    │                              methodologies: Method A (group-mean of
    │                              property × weight, weight ∈ {raw, freq,
    │                              t}); Method B (composite as synthetic
    │                              auto_aug, plugged into the dashboard's
    │                              pct pipeline — composite min-max scaled
    │                              to [0,1], synth_pct = 100 × Σ(weight ×
    │                              comp_norm) / Σ(weight) — produces a pct
    │                              series structurally identical to real
    │                              pct, eliminating group-size effects).
    │                              Two composites: A = (d·m·s·h)/(r·tf·df),
    │                              B = d·m·s. Each runs full-eco and
    │                              confirmed-only (Schaal Method B parallel
    │                              — restricted to (task, occ) pairs in
    │                              all_confirmed). Plus paper convergence
    │                              rerun: reproduces paper/results/part_1
    │                              convergence + convergence_external
    │                              charts under both freq and t weighting,
    │                              with Composite-A-as-auto-aug as a 5th
    │                              source row. Headlines: (1) raw `s` ranks
    │                              SOC majors at ρ = +0.84 against our pct,
    │                              raw `d` at +0.80 — property signal was
    │                              buried by freq weighting before. (2)
    │                              Composite B (d·m·s) outperforms A at
    │                              every weighting (raw +0.66 vs +0.32,
    │                              ×t +0.71 vs +0.53, Method B ×freq +0.67
    │                              vs +0.39) — friction denominator hurts
    │                              because friction terms have wide per-
    │                              task variance amplified multiplicatively.
    │                              (3) Confirmed-only filter decreases
    │                              strongest predictors (s_raw drops
    │                              −0.19) — restricting to tasks AI sees
    │                              removes discriminative tail. (4) Paper
    │                              convergence with t ≈ freq (internal
    │                              5×5 mean ρ at major: 0.65 vs 0.66;
    │                              external 5×4: 0.69 vs 0.71) — cross-
    │                              source story robust to per-task weight.
    │                              (5) all_confirmed_conservative tracks
    │                              all_confirmed almost identically; t-
    │                              weighted composite slightly stronger.
    │                              Headline single number: ρ +0.71 at
    │                              major (Method A, Composite B, ×t, full
    │                              eco) — what 12 LLM-rated properties +
    │                              one slim formula can do without seeing
    │                              any usage data. 6 PNGs + 6 CSVs.
    ├── crashing_waves_vs_rising_tides/ — Empirical comparison to Mertens et
    │                              al. (2026), "Crashing Waves vs. Rising
    │                              Tides" (arXiv 2604.01363). Two parts.
    │                              Part A tests cross-occupation distribution
    │                              shape of Δpct_tasks_affected between
    │                              snapshots — histograms with shape stats
    │                              (Gini/kurtosis/skew/concentration), Lorenz
    │                              curves, lift profile by initial-exposure
    │                              decile, rank stability over time,
    │                              per-period violins, growth-by-major
    │                              sorted by paper β. Run for both
    │                              `all_confirmed` (4 dates) and `all_ceiling`
    │                              (8 dates). Headline: capability (ceiling)
    │                              is tide-shaped (Gini 0.39, smooth lift),
    │                              adoption (confirmed) is wave-shaped
    │                              (Gini 0.65, concentrated in already-
    │                              exposed occupations). Part B encodes
    │                              Mertens Table 1 betas per major and
    │                              computes three forward-risk scores per
    │                              occupation restricted to the six sig-β
    │                              majors: already_score = pct × |β|,
    │                              headroom_score = (100−pct) × |β|,
    │                              combined_score = p(1−p)|β|·100. 13 PNGs
    │                              + 11 CSVs. The "already" cut surfaces
    │                              the most policy-relevant front-of-the-
    │                              wave list (Electronics Engineers,
    │                              Investment Fund Managers, Architects,
    │                              Graphic Designers, PR Specialists,
    │                              Concierges); the "headroom" cut is
    │                              dominated by Personal Care/Service
    │                              because |β|=0.93 there is roughly double
    │                              the next steepest.
    └── pct_norm_vs_eco/         — AI usage distribution (Σ pct_normalized) vs. economic
                                   baseline (freq×emp / freq-allocated emp), renormalized
                                   to 100%. Overhauled: two configs (all_confirmed and
                                   aei_all_usage), seven levels (major/minor/broad/occ/
                                   gwa/iwa/dwa), two eco scopes (config-scoped vs. full
                                   eco_2025), and five bias variants (no_bias, equal
                                   3-source consensus, chatgpt_2x/5x/10x). Bias correction
                                   divides each task's pct by bias_ratio[gwa] =
                                   claude_share / consensus_share, averaging across GWAs
                                   for multi-mapped tasks at occ-hierarchy levels. Source
                                   GWA shares (AEI, Copilot, ChatGPT) hardcoded from
                                   published distributions. Coverage: GWA + major have
                                   all bias × both configs × both eco (40 charts each);
                                   other levels are all_confirmed only, equal bias only,
                                   both eco (4 charts each × 5 = 20). 100 PNGs total.
                                   V2 add-on (run_v2.py + pct_norm_vs_eco_report_v2.md):
                                   20 intensity-ranking charts + diagnostics table. Per-cat
                                   ratio = Σ pct (bias-corrected) / Σ (freq×emp), renormed
                                   to 100%. Single-color horiz bar, top-30 + bot-10.
                                   Coverage: 8 base levels (major/minor/broad/occ/gwa/iwa/
                                   dwa/task) with config-scoped denominator, +2 ChatGPT-5×
                                   variants, +2 full eco_2025 denominator variants, +4
                                   auto_aug-weighted variants, +4 smoothing variants (sqrt
                                   and additive shrinkage with α=median den on major + gwa).
                                   Plus major_diagnostics.csv + major_raw_numerator.png
                                   showing per-major task counts, eco coverage, raw Σ pct
                                   (with and without auto_aug), and all three ratio
                                   variants' shares. Same bias-correction code as v1.
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
- **SKA category analysis uses ai_pct_occ (not ai_pct_eco_mean)**: When computing SKA averages by occupation category, use `ai_pct_occ` (per-occ: ai_score / occ_score × 100) averaged across occupations. Do not use `ai_pct_eco_mean` (which divides by the mean occ_score across all occupations, not the specific occupation's score). The two are different and produce different category rankings.
- **all_confirmed series starts at March 2025**: The 2024-09-30 and 2024-12-23 dates have been removed from all trend series. The September 2024 date was anchored by Microsoft Copilot only (AEI conversation and API data starts accumulating from December 2024), and December 2024 is similarly excluded. The series now starts at March 2025, where AEI + Microsoft data is available for all_confirmed. Do not re-add either 2024 date to any trend series.
