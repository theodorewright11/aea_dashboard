# Part 1 — Scale, Convergence, Growth

First section of the Results chapter. Charts only (no prose yet).

## Charts Produced

| Figure | What It Shows |
|--------|--------------|
| `overview.png` | Five-config aggregate footprint: workers and wages as % of national totals |
| `convergence.png` | 2x2 Spearman rank correlation heatmaps (lower triangle) across four independent sources at four aggregation levels |
| `temporal_trend.png` | Line chart: % of employment with AI-exposed tasks over time (All Confirmed vs All Ceiling) |
| `temporal_deltas.png` | Table: per-date changes in tasks, workers, wages, and % employment |

## Config

All charts: National | Freq | Auto-aug ON

**Overview configs:** All Confirmed, All Ceiling, Human Conversation, Agentic Confirmed, Agentic Ceiling

**Correlation sources:** Claude (AEI Conv cumul.), Claude API (AEI API cumul.), Copilot (Microsoft), MCP (MCP Cumul. v4)

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_1.run
```
