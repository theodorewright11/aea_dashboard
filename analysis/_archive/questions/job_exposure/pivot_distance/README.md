# Pivot Distance

**Question:** How costly is it to reskill from a high-risk job to a low-risk job in the same zone?

Computes an average "pivot cost" per job zone — the total skill and knowledge gap a worker in a high-risk occupation would need to close to reach the nearest low-risk occupation in the same zone. Lower job zones have lower-cost pivots because the knowledge is less specialized.

Uses Skills + Knowledge elements (importance ≥ 3). Abilities excluded (less trainable).

## Method

For each job zone:
1. Identify top 10 highest-risk occupations (by risk_score from job_risk_scoring)
2. Identify bottom 10 lowest-risk occupations (by risk_score)
3. Compute average skill+knowledge profile for each group
4. For each element: `element_cost = max(0, low_risk_avg_score − high_risk_avg_score)`
5. `pivot_cost = sum of element_costs` across all elements

## Key outputs

| File | Description |
|------|-------------|
| `results/pivot_cost_by_zone.csv` | Job zone, avg pivot cost, example high/low risk occs |
| `results/element_costs_by_zone.csv` | Per-element cost breakdown per job zone |
| `results/high_risk_profiles.csv` | Skill+knowledge profiles of top-10 high-risk occs per zone |
| `results/low_risk_profiles.csv` | Same for bottom-10 low-risk |
| `figures/pivot_cost_by_zone.png` | Bar chart: average pivot cost by job zone |
| `figures/element_cost_heatmap.png` | Heatmap: which elements drive cost in each zone |

## Run

```bash
venv/Scripts/python -m analysis.questions.job_exposure.pivot_distance.run
```
