# Activity Robustness

**Question:** Which work activities are AI-resistant, and which are in the next wave?

Tiers the full IWA set by confirmed exposure, identifies activities that are stable-robust across all 5 configs, and surfaces the "next wave" — activities where the ceiling exposure already exceeds 33% even though confirmed usage is still below.

Thresholds: Robust < 33% | Moderate 33–66% | Fragile ≥ 66%

## Outputs

| File | Description |
|------|-------------|
| `results/iwa_robustness.csv` | All IWAs: confirmed pct, tier, ceiling pct, gap |
| `results/iwa_tier_stability.csv` | Cross-config tier counts per IWA |
| `results/gwa_robustness.csv` | GWA-level tier assignments |
| `results/next_wave_iwas.csv` | IWAs currently robust but ceiling ≥ 33% |

## Figures

| File | Description |
|------|-------------|
| `figures/iwa_robustness_tiers.png` | All IWAs colored by tier |
| `figures/next_wave_gaps.png` | Next wave IWAs: confirmed vs ceiling gap |
| `figures/gwa_robustness.png` | GWA-level robustness overview |
| `figures/cross_config_stability.png` | Cross-config spread per IWA |

## Run

```bash
venv/Scripts/python -m analysis.questions.work_activity_exposure.activity_robustness.run
```
