# Audience Framing

**Question:** How do work activity exposure findings translate for each audience?

Four framings, each with dedicated statistics and figures:
- **Policy/legislators** — Where should training dollars go? Which GWAs represent the largest workforce × exposure combination?
- **Workforce/educators** — Which activity clusters to invest in; the training sweet spot
- **Researchers** — Config agreement/disagreement at GWA level; what the data supports vs. doesn't
- **Laypeople** — Is AI a fad? GWA trends over time showing whether exposure is growing

## Outputs

| File | Description |
|------|-------------|
| `results/policy_key_stats.csv` | High-level policy statistics |
| `results/workforce_training_sweet_spot.csv` | Robust IWAs with large workforce |
| `results/researcher_config_spread.csv` | GWA-level config spread and CV |
| `results/layperson_gwa_summary.csv` | GWA summary for lay audience |

## Figures

| File | Description |
|------|-------------|
| `figures/policy_gwa_workers.png` | Policy: top GWAs by workers affected |
| `figures/workforce_training_targets.png` | Workforce: training sweet spot |
| `figures/researcher_config_comparison.png` | Researcher: config spread dotplot |
| `figures/layperson_ai_trend.png` | Layperson: GWA exposure over time |

## Run

```bash
venv/Scripts/python -m analysis.questions.work_activity_exposure.audience_framing.run
```
