# Job Structure

**Question:** How do job zones and job outlook distribute across AI exposure levels and sectors?

Uses O*NET job zones (1–5, preparation required) and Utah DWS outlook ratings (1–3; 1=bright/high-wage, 2=average, 3=below average) to show structural correlates of AI exposure.

## Key outputs

| File | Description |
|------|-------------|
| `results/occ_structural.csv` | Per-occ: pct, job_zone, outlook, emp, major, tier |
| `results/zone_tier_distribution.csv` | Count/workers by (job_zone × exposure tier) |
| `results/outlook_tier_dist.csv` | Count/workers by (outlook × exposure tier) |
| `results/major_zone_pct.csv` | Avg pct_tasks_affected by (major, job_zone) |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/zone_exposure_violin.png` | Pct distribution by job zone (emp-weighted) |
| `figures/outlook_exposure_violin.png` | Pct distribution by outlook rating |
| `figures/zone_tier_heatmap.png` | Workers by (job_zone × exposure tier) |
| `figures/outlook_tier_heatmap.png` | Workers by (outlook × exposure tier) |
| `figures/major_zone_heatmap.png` | Avg pct by (sector × job zone) |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.job_structure.run
```
