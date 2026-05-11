# Part 1 — Scale, Convergence, Growth

First section of the Results chapter. First draft complete. Content in `part_1.md`.

## Charts Produced

| Figure | What It Shows |
|--------|--------------|
| `overview.png` | Five-config aggregate footprint: % tasks, workers, and wages as % of national totals (blue/teal/gold bars) |
| `convergence.png` | 2x2 Spearman rank correlation heatmaps (lower triangle) across four independent sources at four aggregation levels |
| `convergence_external.png` | 2x2 grid of rectangular 4x4 heatmaps — our four sources (rows) vs. four external academic benchmarks (cols: Eloundou GPT-4 β, Eloundou Human β, AIOE mean, AIOE Reading Comprehension) at four aggregation levels |
| `temporal_trend.png` | Three-panel line chart (% tasks / workers / wages) over time, All Confirmed (solid) vs All Ceiling (dashed). Each line is extended past its final observation with a dotted linear OLS projection marking 6mo / 1yr / 2yr horizons (assumes recent rate continues). |
| `temporal_table_all_confirmed.png` | Growth data table for All Confirmed: tasks, workers, wages, auto-aug, coverage per date |
| `temporal_table_all_ceiling.png` | Growth data table for All Sources (Ceiling): same columns |

## Config

All charts: National | Freq | Auto-aug ON

**Overview:** % Tasks Affected = unweighted mean across occupations. Workers/Wages % = employment/wage-weighted.

**Correlation sources:** Claude (AEI Conv 2026-02-12), Claude API (AEI API 2026-02-12), Copilot (Microsoft), MCP (MCP Cumul. v4)

**External benchmarks:** Eloundou et al. 2023 (`gpts_are_gpts_occ_data.csv`, `dv_rating_beta` and `human_rating_beta`, scaled ×100); AIOE (Felten/Raj/Seamans) — per-occupation score = sum(imp×lv×ability_cap) / sum(imp×lv) over imp≥3 ability rows, using `aioe_ability_matrix.csv` row mean and the Reading Comprehension column. External benchmarks are rolled up from occupation level to SOC group level using an unweighted mean across matched occupations (matches the exploratory gpts_are_gpts and aioe_comparison conventions).

**Tables:** Task Coverage = unique tasks in dataset / unique tasks in eco_2025. Auto-aug = mean across unique tasks. Delta workers/wages show absolute + % change.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_1.run
```
