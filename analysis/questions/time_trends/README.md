# Time Trends

**Overarching question:** What does the temporal dimension reveal that static snapshots miss — how did AI exposure evolve, which occupations followed which growth patterns, and what's the trajectory of the confirmed/ceiling gap?

This bucket uses the full `ANALYSIS_CONFIG_SERIES` time series rather than single-point-in-time configs. Primary lens is `all_confirmed` (AEI Both + Micro, Sep 2024 – Feb 2026).

## Sub-Analyses

| Sub-folder | Question |
|------------|----------|
| `trajectory_shapes/` | How did individual occupations grow? Six trajectory type classifications across 923 occupations |
| `tier_churn/` | How stable are exposure tiers? Tier transitions, new high-tier entrants, sector stability |
| `confirmed_ceiling_convergence/` | Is deployment catching up to capability? Confirmed/ceiling ratio trends nationally and by sector |
| `wa_tipping_points/` | Which work activities crossed meaningful thresholds, and which are approaching them? |
| `occs_timeline/` | Full time-series for the 29 named occupations of interest |

## Running Scripts

From the project root:

```bash
venv/Scripts/python -m analysis.questions.time_trends.trajectory_shapes.run
venv/Scripts/python -m analysis.questions.time_trends.tier_churn.run
venv/Scripts/python -m analysis.questions.time_trends.confirmed_ceiling_convergence.run
venv/Scripts/python -m analysis.questions.time_trends.wa_tipping_points.run
venv/Scripts/python -m analysis.questions.time_trends.occs_timeline.run
```

## Aggregate Report

See [time_trends_report.md](time_trends_report.md) for the full synthesis.
