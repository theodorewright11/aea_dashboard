# Job Risk Scoring

**Question:** Which jobs are most at risk of replacement (not just transformation)?

Combines seven binary risk factors into a composite score (0–7). High exposure alone doesn't mean replacement — a job needs multiple converging signals: high AI task coverage, a skills profile AI already meets, growing trends, low job-zone barrier, poor outlook, and commoditized tools.

## Risk Factors (7 binary flags)

| # | Flag | At risk if |
|---|------|-----------|
| 1 | pct_tasks_affected | > median across all occs |
| 2 | SKA gap | > median (AI capability exceeds typical job need) |
| 3 | pct trend | positive AND above-median growth (first→last date) |
| 4 | SKA gap trend | positive AND above-median growth |
| 5 | job_zone | ∈ {1, 2, 3} |
| 6 | outlook | ∈ {2, 3} (below avg; outlook 1 = good/low-wage) |
| 7 | n_software | > median |

**Tiers:** 5–7 = High Risk, 3–4 = Moderate, 1–2 = Low

Primary config: `all_ceiling`. Cross-config comparison shows which risk assignments are robust vs. source-dependent.

## Key outputs

| File | Description |
|------|-------------|
| `results/risk_scores_primary.csv` | All 923 occs: 7 flags, risk_score, risk_tier (all_ceiling config) |
| `results/risk_scores_all_configs.csv` | Risk scores for all five configs |
| `results/risk_tier_summary.csv` | Tier counts, employment, wages by tier |
| `results/flags_breakdown.csv` | Which flags are most commonly triggered |
| `figures/risk_tier_distribution.png` | Bar chart of tier distribution |
| `figures/risk_vs_pct_scatter.png` | Scatter: risk_score vs pct_tasks_affected |
| `figures/cross_config_robustness.png` | How risk tier changes across configs |

## Run

```bash
venv/Scripts/python -m analysis.questions.job_exposure.job_risk_scoring.run
```
