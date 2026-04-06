# State Profiles

**Question:** Do states share similar AI exposure profiles? Are there identifiable regional or structural clusters?

## Approach

1. For each of the 50 states + DC, compute major-category pct_tasks_affected using the primary config
2. Build a state × major-category matrix
3. Run k-means clustering (k=5 default, see `N_CLUSTERS` at top of run.py) on the standardized matrix
4. Profile each cluster: what sectors distinguish it from others
5. Rank all states by aggregate workers affected and avg % tasks affected

## Key outputs

| File | Description |
|------|-------------|
| `results/state_totals.csv` | Per-state: workers, wages, pct, cluster |
| `results/state_major_matrix.csv` | State × major pct matrix |
| `results/cluster_assignments.csv` | State → cluster assignment |
| `results/cluster_profiles.csv` | Per-cluster avg pct by major category |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/state_rankings_workers.png` | Top states by workers affected (colored by cluster) |
| `figures/state_rankings_pct.png` | Top states by avg % tasks affected |
| `figures/cluster_heatmap.png` | Heatmap: cluster × major, avg pct (cluster profiles) |
| `figures/state_cluster_map.png` | Strip plot: states by cluster and pct |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.state_profiles.run
```

Note: requires `scikit-learn` (`pip install scikit-learn`).
