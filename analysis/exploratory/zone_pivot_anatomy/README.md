# zone_pivot_anatomy — Why Zone 3 Peaks on Pivot Cost

Diagnostic deep-dive into the pivot_distance finding that Zone 3 workers face
the most expensive reskilling path (359 units), higher than Zones 4 and 5
despite those zones having deeper/more complex SKA profiles.

## What it produces

Five figures:

1. **`occ_counts_by_zone_tier.png`** — Occupation counts by job zone × risk tier
   (full distribution, not just the top-10 used in pivot_distance).

2. **`zone_exposure_profiles.png`** — Mean pct_tasks_affected per job zone by
   risk tier group (High, Mod-High, Mod-Low, Low) — shows the exposure spread
   within each zone.

3. **`ska_mass_and_overlap.png`** — Stacked bar showing shared SKA mass vs.
   pivot cost vs. drop cost per zone. Preserves absolute magnitude — answers
   whether Zone 4/5 lower cost comes from smaller raw gaps or more overlap.

4. **`sector_composition_high_risk.png`** — Sector breakdown (by employment) of
   high-risk occupations within each job zone. Shows whether job zone or sector
   is the better targeting variable for retraining investment.

5. **`zone34_scatter.png`** — Scatter of Zone 3 and Zone 4 occupations by
   (pct_tasks_affected, risk_score), colored by sector. Identifies which
   sector × zone combinations are the real retraining targets.

## Config

- **Primary config**: `all_confirmed` — AEI Both + Micro 2026-02-12
- **Risk scoring**: from `job_risk_scoring/results/risk_scores_primary.csv`
- **SKA**: `compute_ska()` fresh, importance >= 3
- **Pivot groups**: same top-10 high/low risk per zone as `pivot_distance/`

## Run

```
venv/Scripts/python -m analysis.exploratory.zone_pivot_anatomy.run
```

Outputs saved to `results/figures/`.
