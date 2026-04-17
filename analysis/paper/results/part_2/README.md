# Part 2 — Characterization: Where AI Exposure Falls

Five chart groups characterizing the structural distribution of AI exposure.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `phys_info_divide.png` | Box plots of % tasks affected by occupation group (Non-physical / Mixed / Physical), classified by proportion of physical tasks (<33% / 33-67% / >67%) |
| `job_zone_violin.png` | Violin plots of % tasks affected by O*NET job zone (1-5), with n, median, and mean annotations |
| `ska_levels.png` | AI Maximum of imp×lv vs. workforce benchmarks (max, P95, top-10, mean) for every Skills, Abilities, and Knowledge element (3 subplots, importance ≥ 3 filter) |
| `gwa_exposure.png` | All General Work Activities ranked by % tasks affected, bar color intensity = workers affected, annotated with workers and wages |
| `major_categories.png` | All 22 major occupational categories in 3 side-by-side panels: % Tasks Affected, Workers Affected, Wages Affected |

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_2.run
```
