# Part 1 — Scale, Convergence, Growth

First section of the Results chapter. First draft complete. Content in `part_1.md`.

## Charts Produced

| Figure | What It Shows |
|--------|--------------|
| `overview.png` | Five-config aggregate footprint: % tasks, workers, and wages as % of national totals (blue/teal/gold bars) |
| `convergence_major.png`, `convergence_occ.png` | Single-panel Spearman rank correlation heatmap, one file per SOC level (Major, Occupation). Each combines an internal lower-triangle block (4 sources × 4 sources: Claude Browser, Claude API, Copilot, MCP) with a rectangular external block (4 sources × 8 external benchmarks: Eloundou GPT-4 β, Eloundou Human β, AIOE Overall, AIOE Reading Comprehension, Schaal Overall, Schaal DA, Schaal AG, Tomlinson (Copilot)). Minor and Broad levels live in `paperinfra_appendix` (`convergence_full_*`). |
| `convergence_configs_major.png`, `convergence_configs_occ.png` | Same single-panel layout but rows are the 5 ANALYSIS_CONFIGS (All Confirmed, All Sources (Ceiling), Conversational Confirmed, Agentic Confirmed, Agentic Ceiling) instead of the 4 individual sources. Internal lower-triangle 5×5 + external rectangle 5×8. |
| `temporal_trend.png` | Three-panel line chart (% tasks / workers / wages) over time, All Confirmed (solid) vs All Ceiling (dashed). Each line is extended past its final observation with a dotted linear OLS projection, labeled at the 2yr horizon. Confirmed data points are labeled at each spaced observation; ceiling shows only first + last observed labels. |
| `temporal_table_all_confirmed.png` | Growth data table for All Confirmed: tasks, workers, wages, auto-aug, coverage per date |
| `temporal_table_all_ceiling.png` | Growth data table for All Sources (Ceiling): same columns |

## Config

All charts: National | Freq | Auto-aug ON

**Overview:** % Tasks Affected = unweighted mean across occupations. Workers/Wages % = employment/wage-weighted.

**Correlation sources:** Claude (AEI Conv 2026-02-12), Claude API (AEI API 2026-02-12), Copilot (Microsoft), MCP (MCP Cumul. v4)

**External benchmarks:** Eloundou et al. 2023 (`gpts_are_gpts_occ_data.csv`, `dv_rating_beta` and `human_rating_beta`, scaled ×100); AIOE (Felten/Raj/Seamans) — per-occupation score = sum(imp×lv×ability_cap) / sum(imp×lv) over imp≥3 ability rows, using `aioe_ability_matrix.csv` row mean and the Reading Comprehension column; Schaal 2025 (`Comparison of Indices.csv`, `auto_w` overall + `da_w` Data Abundance subhypothesis); Tomlinson, Jaffe, Wang, Counts & Suri 2025 ("Working with AI") AI applicability score (`ai_applicability_scores.csv`) — built on Bing Copilot conversations × O*NET IWA weights, labeled "Tomlinson (Copilot)" because it shares its data family with our internal `Copilot` row. External benchmarks are rolled up from occupation level to SOC group level using an unweighted mean across matched occupations (matches the exploratory gpts_are_gpts and aioe_comparison conventions).

**Tables:** Task Coverage = unique tasks in dataset / unique tasks in eco_2025. Auto-aug = mean across unique tasks. Delta workers/wages show absolute + % change.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_1.run
```
