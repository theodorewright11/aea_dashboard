# Exposure State

**Question:** What is the current state of AI task exposure across occupations?

Measures where work is being transformed today — nationally, time-weighted, auto-aug on. Covers all five dataset configs to show the range from confirmed human usage to the full ceiling of AI capability.

## What this produces

- Tier distribution (High ≥60%, Moderate 40-60%, Restructuring 20-40%, Low <20%) for each of five configs
- How tiers shift across configs (usage floor → capability ceiling)
- Major-category breakdown of tier composition
- Time trend: which occupations are climbing fastest in exposure
- Config comparison scatter showing usage vs. ceiling per occupation

## Key outputs

| File | Description |
|------|-------------|
| `results/all_occupations_exposure.csv` | All 923 occs with pct for all five configs, emp, tier |
| `results/tier_by_config.csv` | Tier counts and employment by config |
| `results/major_tier_rollup.csv` | Tier distribution within each major category |
| `results/pct_trend_by_config.csv` | First-to-last pct growth per occ per config |
| `figures/scatter_exposure_vs_emp.png` | Scatter: pct (all_ceiling) vs employment |
| `figures/tier_stacked_by_major.png` | Stacked bar: tier makeup of each major category |
| `figures/config_comparison.png` | Scatter: human_conversation vs all_ceiling per occ |
| `figures/top_climbers_trend.png` | Top 20 fastest-growing occupations by pct |

## Run

```bash
venv/Scripts/python -m analysis.questions.job_exposure.exposure_state.run
```
