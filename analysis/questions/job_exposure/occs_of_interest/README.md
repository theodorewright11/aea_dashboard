# Occupations of Interest

**Question:** How do all job exposure findings land for the 29 named occupations?

Applies all sub-analyses from the job exposure bucket to a curated list of occupations spanning high-employment, AI-controversial, and Utah-relevant jobs. Produces a focused, presentation-ready summary.

## Occupation List

Defined in `OCCS_OF_INTEREST` in `analysis/config.py`. Three groups:
- **High-profile / high-employment** (12 occs): Registered Nurses, Software Developers, Cashiers, etc.
- **AI-controversial / interesting** (12 occs): Lawyers, Data Scientists, Financial Analysts, etc.
- **Utah-relevant** (5 occs): Computer Systems Analysts, Construction Laborers, etc.

## What this produces

- Exposure state: pct across all five configs for each named occ
- Risk scores and tier for each occ
- SKA gap breakdown: top 5 human-advantage elements and top 5 AI-advantage elements per occ
- Pivot cost for each occ (if their job zone has a computed pivot distance)
- Whether each occ is "hidden at-risk" per audience framing
- Time trend: how each occ's pct has moved

## Key outputs

| File | Description |
|------|-------------|
| `results/occs_of_interest_full.csv` | All metrics for all 29 occupations |
| `results/exposure_by_config.csv` | pct_tasks_affected for each occ × each config |
| `results/risk_scores.csv` | Risk flags and tier per occ |
| `results/ska_gaps.csv` | SKA gap summary per occ |
| `results/trend_summary.csv` | First-to-last pct growth per occ per config |
| `figures/exposure_ranked_bar.png` | Named occs ranked by all_ceiling pct |
| `figures/risk_tier_summary.png` | Named occs colored by risk tier |
| `figures/ska_gap_heatmap.png` | Heatmap: occ × SKA type gap |
| `figures/trend_slopes.png` | Slope chart: pct trend for each named occ |

## Run

Run after `job_risk_scoring` and `worker_resilience`:

```bash
venv/Scripts/python -m analysis.questions.job_exposure.occs_of_interest.run
```
