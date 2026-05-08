# Worker Resilience

**Question:** What can a worker do to make their job more resilient to AI?

For each occupation, ranks Skills, Abilities, and Knowledge elements by the gap between the occupation's need and AI's current capability. Elements where the gap is most negative (human exceeds AI) are where training effort is most valuable. Elements where AI already exceeds the occupation need are where workers should leverage AI rather than compete with it.

Uses all three O*NET types (S + A + K), filtered to importance ≥ 3. Gap = AI capability score − occupation score.

## What this produces

- Per-element gap table for all occupations
- Top elements where human advantage is largest (focus training here)
- Top elements where AI already leads (use AI for these tasks)
- Analysis focused on the occupations of interest list
- Robustness check: how gaps change across the five configs

## Key outputs

| File | Description |
|------|-------------|
| `results/element_gaps_summary.csv` | Mean gap per element across all occupations |
| `results/occ_element_gaps.csv` | Per-occ × element gap detail (all_ceiling config) |
| `results/human_advantage_elements.csv` | Top elements by human advantage (gap < 0) |
| `results/ai_advantage_elements.csv` | Top elements where AI leads (gap > 0) |
| `results/occs_of_interest_gaps.csv` | Gap breakdown for the 29 named occupations |
| `figures/human_advantage_bar.png` | Top 15 elements with largest human advantage |
| `figures/ai_advantage_bar.png` | Top 15 elements AI already covers well |
| `figures/occ_heatmap.png` | Heatmap: occ × element gap for high-risk occupations |

## Run

```bash
venv/Scripts/python -m analysis.questions.job_exposure.worker_resilience.run
```
