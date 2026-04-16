# Part 1 — Scale, Convergence, Growth

First section of the Results chapter. Charts only (no prose yet). Content in `part_1.md`.

## Charts Produced

| Figure | What It Shows |
|--------|--------------|
| `overview.png` | Five-config aggregate footprint: % tasks, workers, and wages as % of national totals (blue/teal/gold bars) |
| `convergence.png` | 2x2 Spearman rank correlation heatmaps (lower triangle) across four independent sources at four aggregation levels |
| `temporal_trend.png` | Line chart: % of employment with AI-exposed tasks over time (All Confirmed vs All Ceiling) |
| `temporal_table_all_confirmed.png` | Growth data table for All Confirmed: tasks, workers, wages, auto-aug, coverage per date |
| `temporal_table_all_ceiling.png` | Growth data table for All Sources (Ceiling): same columns |

## Config

All charts: National | Freq | Auto-aug ON

**Overview:** % Tasks Affected = unweighted mean across occupations. Workers/Wages % = employment/wage-weighted.

**Correlation sources:** Claude (AEI Conv 2026-02-12), Claude API (AEI API 2026-02-12), Copilot (Microsoft), MCP (MCP Cumul. v4)

**Tables:** Task Coverage = unique tasks in dataset / unique tasks in eco_2025. Auto-aug = mean across unique tasks. Delta workers/wages show absolute + % change.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_1.run
```
