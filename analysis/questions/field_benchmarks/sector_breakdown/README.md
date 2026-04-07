# Sector Breakdown

**Question:** Which sectors rank highest across our analysis, Copilot, AEI, and ChatGPT?

Compares sector-level exposure rankings from four sources: our dashboard (BLS major
categories), Copilot's enterprise task applicability data, AEI's task-category
distribution, and ChatGPT's work-session use-type breakdown.

Common finding: Computer/Math, Office/Admin, Sales, and Business/Finance appear
as high-exposure sectors across all sources, though each source has its own
framing and metric.

## Outputs

| File | Description |
|------|-------------|
| `figures/our_sector_rankings.png` | Our top 10 sectors by workers_affected |
| `figures/cross_source_sectors.png` | Our pct vs Copilot applicability for shared sectors |
| `figures/external_task_breakdown.png` | AEI task categories and ChatGPT use types side by side |
| `results/sector_confirmed.csv` | Our sector data (all_confirmed) |
| `results/copilot_sector_data.csv` | Copilot applicability rates |
| `results/aei_task_categories.csv` | AEI task-attempt distribution |
| `results/chatgpt_work_categories.csv` | ChatGPT work-session use types |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.sector_breakdown.run
```
