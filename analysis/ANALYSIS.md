# ANALYSIS.md — AEA Dashboard Analysis System

Reference doc for any Claude Code session working in the `analysis/` folder.

**Before starting, read these files in order:**
1. `CLAUDE.md` (project-wide rules)
2. `PRD.md` (what the dashboard does, all metrics, all pages)
3. `ARCHITECTURE.md` (how the system is built, compute logic, API contracts)
4. This file (how the analysis system works)

---

## 1. What This Is

An organized system for answering research questions using the AEA Dashboard's compute pipeline. Each question lives in its own folder, produces reproducible outputs (CSVs, figures, narrative), and feeds into a rolling report.

This analysis serves three audiences:

- **Supervisors (Alice, Zach)** — They want the actual numbers and reasoning. Show results, get feedback, iterate. They'll push on whether findings are real or artifacts.
- **Policy officials (OAIP staff, Utah policymakers)** — They want clear takeaways and conversation starters, not methodological detail. "Here's what AI is doing to Utah's workforce."
- **The paper** — Dense but understandable. Concise without being ambiguous. Honest about caveats. Someone should be able to recreate the analysis from what's written. Hook with interesting findings, back up with technical depth.

Every finding must be traceable: chart → data → config → computation.

---

## 2. Folder Structure

```
analysis/
├── ANALYSIS.md              — This file
├── config.py                — Shared settings, backend imports, dataset presets
├── utils.py                 — Chart styling, report formatting, common helpers
├── run_all.py               — Regenerates all question outputs
├── questions/
│   ├── _template/           — Copy this to start a new question
│   │   ├── README.md        — Question description, methodology, findings
│   │   ├── run.py           — Generates CSVs + figures
│   │   ├── dashboard.md     — Dashboard settings to reproduce charts on the website
│   │   └── results/
│   │       ├── *.csv
│   │       └── figures/*.png
│   ├── utah_vs_national/
│   ├── top_exposed_occupations/
│   └── ...
└── report/
    ├── report.md            — Rolling narrative report (all questions)
    └── figures/             — Key figures referenced by the report
```

---

## 3. How to Add a New Question

1. Copy `questions/_template/` to `questions/<topic_name>/`
2. Edit `README.md` with the question, why it matters, and methodology
3. Write `run.py` — import from `analysis.config` and `analysis.utils` for shared helpers, import from `backend.compute` for the actual computation
4. Write `dashboard.md` — what controls to set on the website to see equivalent charts (if possible; some analyses won't be reproducible on the dashboard)
5. Run `run.py` to generate CSVs and figures into `results/`
6. Add the question's findings to `report/report.md`

### Running a question script

From the project root:
```bash
venv/Scripts/python -m analysis.questions.<topic_name>.run
```

Or regenerate everything:
```bash
venv/Scripts/python -m analysis.run_all
```

---

## 4. Compute Access

All question scripts import from the backend compute engine. This guarantees analysis results match the dashboard exactly.

### Available imports

```python
# Shared analysis config and helpers
from analysis.config import (
    BACKEND_DIR, DATA_DIR, ANALYSIS_DIR,
    ALL_DATASETS, AEI_DATASETS, MCP_MS_DATASETS,
    WA_AEI_DATASETS, WA_MCP_MS_DATASETS,
    DEFAULT_OCC_CONFIG, DEFAULT_WA_AEI_CONFIG, DEFAULT_WA_MCP_MS_CONFIG,
    make_config, run_occ_query, ensure_results_dir,
)
from analysis.utils import (
    style_figure, save_figure, save_csv, format_workers, format_wages,
)

# Backend compute functions (the same engine the dashboard uses)
from backend.compute import (
    get_group_data,           # occupation-level metrics for a config
    compute_work_activities,  # work activity metrics
    compute_trends,           # time series data
    compute_wa_trends,        # WA time series
    get_explorer_occupations, # all 923 occupations with pre-computed metrics
    get_explorer_groups,      # major/minor/broad group summaries
    get_all_tasks,            # all unique tasks with metrics
    get_all_eco_task_rows,    # all ~23,850 task×occupation rows
    compute_single_dataset,   # single dataset pipeline
    combine_results,          # multi-dataset combination
    load_eco_raw,             # raw eco_2025 DataFrame
    load_eco_baseline,        # deduped eco baseline with task_comp
)
from backend.config import (
    DATASETS, DATASET_SERIES, AGG_LEVEL_COL, SORT_COL_MAP,
)
```

### Convenience wrapper

`run_occ_query(config)` calls `get_group_data()` and renames the internal column to `category`. Returns `(df, group_col)` or `None`. The DataFrame has columns: `category`, `pct_tasks_affected`, `workers_affected`, `wages_affected`, `rank_workers`, `rank_wages`, `rank_pct`.

### Config dict format

The `get_group_data()`, `compute_work_activities()`, and `run_occ_query()` functions take a settings dict:

```python
settings = {
    "selected_datasets": ["AEI v4", "MCP v4", "Microsoft"],
    "combine_method": "Average",     # "Average" | "Max"
    "method": "freq",                # "freq" | "imp"
    "use_auto_aug": True,
    "physical_mode": "all",          # "all" | "exclude" | "only"
    "geo": "nat",                    # "nat" | "ut"
    "agg_level": "major",           # "major" | "minor" | "broad" | "occupation"
    "sort_by": "Workers Affected",  # "Workers Affected" | "Wages Affected" | "% Tasks Affected"
    "top_n": 30,
    "search_query": "",
    "context_size": 3,
}
```

---

## 5. Output Standards

### CSVs
- Always include a header row
- Use descriptive column names (not internal codes)
- Include a `_metadata` row or comment at the top if it helps interpretability
- Round floats to 2 decimal places for display-oriented CSVs

### Figures
- Use `utils.save_figure()` which applies consistent professional styling
- High resolution (300 DPI) for paper/print use
- Include clear titles, axis labels, and source attribution
- Color palette should be consistent across all questions
- Save as PNG

### README.md (per question)
Structure:
```markdown
# Question: <clear statement of what we're investigating>

## Why This Matters
<1-2 paragraphs: policy relevance, what decisions this informs>

## Methodology
<What data, configs, and computations were used. Enough to reproduce.>

## Key Findings
<Numbered findings with supporting data references>

## Caveats
<What this analysis does NOT show, limitations, things to be careful about>

## Files
<List of output CSVs and figures with one-line descriptions>
```

### dashboard.md (per question)
```markdown
# Dashboard Instructions: <question name>

## Chart 1: <description>
- **Page:** Occupation Categories / Work Activities / Trends
- **Group A:** datasets=..., method=..., geo=..., agg=..., etc.
- **Group B:** (if applicable)
- **Sort by:** ...
- **Top N:** ...
- **Note:** <any differences from the analysis output>
```

---

## 6. Report

`report/report.md` is the rolling narrative that combines all question findings. Structure:

```markdown
# AEA Dashboard Analysis Report

## Executive Summary
<Key takeaways across all questions — written for the policy audience>

## Table of Contents
<Links to each section; this defines presentation order>

## [Section per question]
### <Question title>
<Narrative incorporating findings, figures, and data references>

## Methodology Notes
<Shared methodology context that applies across questions>

## Appendix
<Additional tables, extended data, technical notes>
```

The TOC controls the order questions appear in the report. Questions can be reordered by editing the TOC without renaming folders.

---

## 7. Style Guidelines

### For figures going into presentations (OAIP audience)
- Large, readable fonts
- Minimal clutter — no gridlines unless they help
- Clear takeaway in the title (not just "Workers Affected by Major Category" but "Management Occupations Have the Most AI-Exposed Workers")
- Color-code meaningfully (e.g., Utah vs National, different dataset families)

### For figures going into the paper
- Grayscale-friendly (or use patterns alongside color)
- Include figure numbers and captions
- Source attribution in small text below

### For CSV tables (supervisor audience)
- Include all the numbers — don't round too aggressively
- Include rank columns where relevant
- Make it filterable/sortable (just good CSV hygiene)

---

## 8. Common Pitfalls

- **pct_tasks_affected must be ratio-of-totals**, never average-of-percentages. If you're computing a group-level pct, re-derive it from summed task_comps, don't average occupation-level pcts.
- **AEI and MCP/Microsoft can't be mixed for work activity analysis** — they use different task baselines (O*NET 2015 vs 2025).
- **Only one cumulative AEI version at a time** — v4 includes all prior data.
- **Only one MCP version at a time** for charts (trends use all versions).
- **Explorer metrics are pre-computed** across all 8 sources. For custom configs, use `get_group_data()` or `compute_single_dataset()`.
- **Auto-aug scores are 0-5** — divide by 5 to get the multiplier.
- **pct_normalized is already in percent form** — 0.4 means 0.4%, not 40%.
