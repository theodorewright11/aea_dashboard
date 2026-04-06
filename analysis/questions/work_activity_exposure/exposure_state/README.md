# Exposure State

**Question:** What is the current state of AI task exposure across work activities?

Ranks IWAs (Intermediate Work Activities) by % tasks affected and workers affected across all five canonical configs. GWA summaries for overview; DWA data for deep-dive.

Primary config: `all_confirmed` (AEI Both + Micro 2026-02-12).

## Outputs

| File | Description |
|------|-------------|
| `results/iwa_all_configs.csv` | All IWAs × 5 configs (pct, workers, wages) — wide format |
| `results/gwa_all_configs.csv` | All GWAs × 5 configs — wide format |
| `results/dwa_confirmed.csv` | All DWAs for primary config |
| `results/iwa_trends_confirmed.csv` | IWA trends over time (all_confirmed series) |
| `results/iwa_confirmed_vs_ceiling.csv` | IWA confirmed % vs ceiling % with gap |

## Figures

| File | Description |
|------|-------------|
| `figures/top_iwas_pct.png` | Top 20 IWAs by % tasks affected |
| `figures/top_iwas_workers.png` | Top 20 IWAs by workers affected |
| `figures/gwa_config_comparison.png` | GWA exposure across all 5 configs (grouped bar) |
| `figures/iwa_trends.png` | Exposure trends over time for top IWAs |
| `figures/iwa_confirmed_vs_ceiling.png` | Scatter: confirmed vs ceiling per IWA |

## Run

```bash
venv/Scripts/python -m analysis.questions.work_activity_exposure.exposure_state.run
```
