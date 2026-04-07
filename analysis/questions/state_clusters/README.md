# State Clusters

**Overarching question:** When you examine U.S. states through the lenses established in the other analyses — risk landscape, work activity fingerprint, agentic exposure, adoption gap — do the same state groupings emerge each time, or does each lens reveal different fault lines?

The `economic_footprint/state_profiles` analysis established five state clusters based on *sector composition* of each state's AI-exposed workforce. That analysis found average task exposure is uniform (~36.1%) across all states — what varies is the type of exposed work. This bucket pushes that finding further: it produces an independent clustering on each analytical dimension, then asks where the clusterings agree or diverge.

---

## Sub-questions

| Sub-folder | Clustering dimension |
|---|---|
| `risk_profile/` | Employment-weighted share of workers in each risk tier (high/moderate/low) |
| `activity_signature/` | GWA-level share of affected employment (what types of work AI is touching) |
| `agentic_profile/` | Agentic intensity per sector (agentic workers / confirmed workers ratio, by sector) |
| `adoption_gap/` | Gap intensity per sector (ceiling - confirmed gap, relative, by sector) |
| `cluster_convergence/` | Cross-clustering comparison: which states group consistently vs. which flip by lens |

## Reference

The sector-composition baseline clustering is in `economic_footprint/state_profiles/`. All sub-questions here compare their new cluster assignments back to those five groups.

## Run order

Run sub-questions 1–4 first (any order), then `cluster_convergence/` last.

```
venv/Scripts/python -m analysis.questions.state_clusters.risk_profile.run
venv/Scripts/python -m analysis.questions.state_clusters.activity_signature.run
venv/Scripts/python -m analysis.questions.state_clusters.agentic_profile.run
venv/Scripts/python -m analysis.questions.state_clusters.adoption_gap.run
venv/Scripts/python -m analysis.questions.state_clusters.cluster_convergence.run
```
