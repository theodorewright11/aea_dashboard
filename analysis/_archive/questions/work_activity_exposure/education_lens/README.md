# Education Lens

**Question:** What does work activity exposure mean for what we teach and train?

Three angles:
1. What fraction of the workforce is primarily doing high-exposure activities?
2. Which IWAs are durable training targets (robust across all 5 configs, with large workforce)?
3. Is AI's footprint expanding into new activity categories, or deepening in existing ones?

Also classifies GWAs into domains (Cognitive/Technical · Information/Documentation · Interpersonal · Management/Coordination · Physical/Operational) to understand which broad domains of work are most/least exposed.

## Outputs

| File | Description |
|------|-------------|
| `results/workforce_by_tier.csv` | Workers in each exposure tier |
| `results/durable_training_targets.csv` | IWAs robust in all 5 configs, ranked by workers |
| `results/gwa_domain_classified.csv` | GWAs with domain classification and exposure |
| `results/iwa_growth.csv` | Per-IWA growth from first to last date in all_confirmed series |
| `results/domain_exposure_summary.csv` | Domain-level avg pct and workers |

## Figures

| File | Description |
|------|-------------|
| `figures/workforce_by_tier.png` | Bar: workers in each IWA exposure tier |
| `figures/durable_training_targets.png` | Durable IWAs to train toward |
| `figures/exposure_growth_trend.png` | Fastest-growing IWAs vs stable-low IWAs |
| `figures/domain_exposure.png` | Avg exposure by work domain |

## Run

```bash
venv/Scripts/python -m analysis.questions.work_activity_exposure.education_lens.run
```
