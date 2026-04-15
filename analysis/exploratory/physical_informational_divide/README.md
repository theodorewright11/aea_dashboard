# Exploratory: Physical vs. Informational Divide

## What it produces

Classifies all 923 O*NET occupations into physical, mixed, or non-physical groups
based on the share of their tasks carrying the O*NET `physical` flag. For each of
the six (occ_group × task_type) combinations, shows the distribution of tasks
across GWA, IWA, and DWA categories — purely structural task counts, no AI
scoring. Also compares average auto-aug score across the three groups.

**Occupation thresholds (% of tasks that are physical):**
- Non-physical: < 33%  →  461 occupations
- Mixed: 33–67%        →  267 occupations
- Physical: > 67%      →  187 occupations

**Figures:**
- `gwa_task_distribution.png` — 3×2 panel, top-15 GWAs per combination
- `iwa_task_distribution.png` — 3×2 panel, top-12 IWAs per combination
- `dwa_task_distribution.png` — 3×2 panel, top-10 DWAs per combination
- `auto_aug_by_occ_group.png` — mean auto-aug by occupation group (3 bars)

## Config used

- Dataset: `final_all_confirmed_usage_2026-02-12.csv` (All Confirmed primary config)
- Task classification: O*NET 2025 `physical` boolean flag on each task row

## Run command

From project root:

```
venv/Scripts/python -m analysis.exploratory.physical_informational_divide.run
```

Results are saved to `results/` (gitignored). Key figures are copied to
`figures/` (committed) and embedded in the report.
