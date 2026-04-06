# Trends

**Question:** How are workers/wages/% tasks affected changing over time across sectors and all five dataset configs?

## Approach

- Aggregate national totals at every date in each config's time series (ANALYSIS_CONFIG_SERIES)
- Major category breakdown over time for the primary config (all_confirmed) only — too many lines for cross-config
- Identify top 10 fastest-growing major categories by absolute percentage-point gain

## Key outputs

| File | Description |
|------|-------------|
| `results/aggregate_trend.csv` | Workers/wages/pct per (config, date) |
| `results/major_trend_confirmed.csv` | Major × date for all_confirmed series |
| `results/major_growth.csv` | Major categories ranked by pct gain |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/aggregate_trend.png` | Workers affected over time, all configs |
| `figures/aggregate_trend_pct.png` | Avg % tasks affected over time, all configs |
| `figures/major_trends_confirmed.png` | Top 10 growing sectors (all_confirmed) |
| `figures/major_growth_bar.png` | Bar chart of absolute pct gain by sector |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.trends.run
```
