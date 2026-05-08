# Utah Benchmarks

**Question:** What does AI task exposure look like for Utah workers specifically, and how does it compare to Seampoint?

Focuses on `pct_tasks_affected` for Utah workers — the employment-weighted share of tasks
that AI is touching — and benchmarks it against Seampoint's 20% takeover / 51% augment
estimates. Complements `wage_impact/` which covers the dollar dimension.

Also shows which Utah occupations are most exposed under the All Confirmed config.

## Outputs

| File | Description |
|------|-------------|
| `figures/utah_pct_comparison.png` | Our 5 configs Utah pct_agg vs Seampoint 20%/51% |
| `figures/utah_top_occs.png` | Top 20 Utah occupations by pct_tasks_affected |
| `results/utah_pct_agg.csv` | pct_agg, workers, wages by config for Utah |
| `results/utah_top_occs_confirmed.csv` | All Utah occupations ranked by exposure |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.utah_benchmarks.run
```
