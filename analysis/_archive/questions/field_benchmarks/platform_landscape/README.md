# Platform Landscape

**Question:** How does the AEA Dashboard fit within the full landscape of AI-and-work research?

The capstone sub-folder for `field_benchmarks/`. Synthesizes all six external sources
and our five configs into a single comparative view — methodology map, headline number
comparison, and a rendered source summary table.

Useful for presentations, briefings, or anyone asking "how does your work relate to X?"

## Outputs

| File | Description |
|------|-------------|
| `figures/headline_comparison.png` | All sources' headline % on one chart |
| `figures/methodology_map.png` | Scatter: measurement type vs. exposure rate, all sources |
| `figures/source_summary_table.png` | Rendered methodology comparison table |
| `results/platform_comparison_table.csv` | Full comparison data |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.platform_landscape.run
```
