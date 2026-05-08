# Automation Share

**Question:** How does our confirmed task-exposure rate compare to external benchmarks?

Compares our employment-weighted mean `pct_tasks_affected` across all five analysis
configs against Project Iceberg's skill-value substitutability index and Seampoint's
governance-constrained deployment estimate.

The three sources measure genuinely different things:
- **Ours**: confirmed real-world AI usage cross-walked to BLS tasks
- **Iceberg**: technical capability of AI tools to perform skill wage value
- **Seampoint**: governance-constrained deployment readiness for Utah

## Outputs

| File | Description |
|------|-------------|
| `figures/rate_comparison.png` | All 5 configs vs external benchmarks (horizontal bar) |
| `figures/layer_chart.png` | Dot plot spectrum from agentic_confirmed to Seampoint augment |
| `results/automation_share_ours.csv` | Our 5 configs pct_agg |
| `results/external_benchmarks.csv` | External source values with metric basis |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.automation_share.run
```
